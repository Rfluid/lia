import logging
from collections import Counter
from typing import cast

from fastapi import HTTPException
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver  # ⇐ postgres backend
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from psycopg import Connection, connect
from psycopg.rows import DictRow, dict_row

from src.agent.model.chat_interface import ChatInterface
from src.agent.model.graph_state import GraphState
from src.agent.model.steps import Steps
from src.agent.model.tool_data import ToolData
from src.config import env
from src.error_handler import ErrorHandler
from src.evaluate_tools.main import EvaluateTools
from src.generate_response import ResponseGenerator
from src.system_prompt.main import SystemPromptBuilder
from src.vector_manager.main import VectorManager

# from psycopg import Connection  # ⇐ open sync conn
# from psycopg.rows import dict_row  # ⇐ row factory

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,  # or DEBUG
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class Workflow(SystemPromptBuilder):
    tool_evaluator: EvaluateTools
    response_generator: ResponseGenerator
    graph: StateGraph
    compiled_graph: CompiledStateGraph
    memory: BaseCheckpointSaver
    vector_manager: VectorManager

    def __init__(self) -> None:
        super().__init__()
        self.tool_evaluator = EvaluateTools()
        self.response_generator = ResponseGenerator()
        self.vector_manager = VectorManager()
        self.error_handler = ErrorHandler()
        self.graph = self._load_graph()
        self.memory = self._load_memory()
        self.compiled_graph = self.graph.compile(checkpointer=self.memory)

    def context_incrementer(self, state: GraphState) -> GraphState:
        state.step_history.append(Steps.context_incrementer)
        state.messages = state.input

        if state.function == "context_incrementer":
            state.next_step = Steps.end
            return state

        state.next_step = Steps.context_builder
        return state

    # Build the context for the AI.
    def context_builder(self, state: GraphState) -> GraphState:
        state.step_history.append(Steps.context_builder)

        # Check if the universal context have been passed
        if len(state.messages) > 2:
            return state

        agent_context = SystemMessage(content=self.prompt)
        state.messages = [agent_context]

        return state

    def generate_response(self, state: GraphState) -> GraphState:
        state.step_history.append(Steps.generate_response)
        try:
            match state.chat_interface:
                case ChatInterface.api:
                    response = self.response_generator.generate_response(
                        self.compiled_graph.config,
                        state.messages,
                    )
                # case ChatInterface.whatsapp:
                #     response = self.response_generator.generate_whatsapp_response(
                #         self.compiled_graph.config,
                #         state.messages,
                #     )

            state.next_step = Steps(response.next_step)

            ai_message = AIMessage(content=[response.model_dump()])
            state.response = ai_message
            state.messages = [ai_message]
        except Exception as e:
            state.error = str(e)
            state.next_step = Steps.error_handler

        return state

    def decide_next_step(self, state: GraphState) -> GraphState:
        state.step_history.append(Steps.evaluate_tools)
        try:
            # Preventing double injection of context and loops
            if self._is_looping(
                state.step_history,
                state.loop_threshold,
            ):
                raise ValueError(
                    f"Loop detected in step history: {state.step_history}. "
                    f"The loop threshold ({state.loop_threshold}) was exceeded due to repeated steps."
                )
            # if state.previous_step == Steps(response.tool):
            #     state.previous_step = Steps.evaluate_tools
            #     raise ValueError("Loop detected: Tool already used.")

            response = self.tool_evaluator.decide_next_step(
                self.compiled_graph.config,
                state.messages,  # Verify need
            )

            ai_message = SystemMessage(content=[response.model_dump()])
            state.messages = [ai_message]

            state.next_step = Steps(response.tool)
            rag_query = response.rag_query
            if rag_query is not None:
                state.tool_payloads.rag_query = rag_query

        except Exception as e:
            state.error = str(e)
            state.next_step = Steps.error_handler

        return state

    def rag(self, state: GraphState) -> GraphState:
        state.step_history.append(Steps.rag)
        try:
            query = state.tool_payloads.rag_query
            if not isinstance(query, str):
                raise ValueError("Expected the query to be a string.")

            logger.info(f"Running RAG retrieval for query: {query}")

            # Retrieve relevant documents from the vectorstore
            retrieved_docs = self.vector_manager.retrieve(
                query=query, top_k=state.top_k
            )

            logger.info(f"Retrieved {len(retrieved_docs)} documents.")

            # Create a new SystemMessage with the retrieved documents
            documents_message = SystemMessage(
                content=[
                    str(
                        ToolData(
                            data=retrieved_docs,
                            label=f"Knowledge base documents retrieved for: '{query}'",
                        )
                    )
                ]
            )

            # Update the messages in state
            state.messages = [documents_message]
            state.next_step = Steps.evaluate_tools

        except Exception as e:
            logger.error(f"Error during RAG retrieval: {str(e)}", exc_info=True)
            state.error = str(e)
            state.next_step = Steps.error_handler

        return state

    def handle_error(self, state: GraphState) -> GraphState:
        state.step_history.append(Steps.error_handler)
        logging.info("entered error handling")
        if state.error is None:
            raise ValueError("No error to handle.")

        if state.current_retries >= state.max_retries:
            logging.exception("current retries exceeded")
            raise HTTPException(status_code=500, detail=state.error)

        state.current_retries += 1

        handling_context = self.error_handler.handle(state.error)

        state.messages = [handling_context]

        state.next_step = Steps.evaluate_tools

        return state

    def _is_looping(self, step_history: list[Steps], threshold: int) -> bool:
        counts = Counter(step_history)
        most_common_step, count = counts.most_common(1)[0]
        return count > threshold

    # ---------- internal helpers ---------- #
    def _load_graph(self) -> StateGraph:
        graph = StateGraph(GraphState)

        # Setup nodes
        graph.add_node(str(Steps.context_incrementer), self.context_incrementer)
        graph.add_node(str(Steps.context_builder), self.context_builder)
        graph.add_node(str(Steps.evaluate_tools), self.decide_next_step)
        graph.add_node(str(Steps.generate_response), self.generate_response)
        graph.add_node(str(Steps.rag), self.rag)
        graph.add_node(str(Steps.error_handler), self.handle_error)

        # Setup edges
        graph.set_entry_point(str(Steps.context_incrementer))
        graph.add_conditional_edges(
            str(Steps.context_incrementer),
            lambda x: x.next_step,
            {
                Steps.context_builder: str(Steps.context_builder),
                Steps.end: END,
            },
        )
        graph.add_edge(str(Steps.context_builder), str(Steps.evaluate_tools))
        graph.add_conditional_edges(
            str(Steps.evaluate_tools),
            lambda x: x.next_step,
            {
                Steps.rag: str(Steps.rag),
                Steps.generate_response: str(Steps.generate_response),
                Steps.error_handler: str(Steps.error_handler),
            },
        )
        graph.add_conditional_edges(
            str(Steps.rag),
            lambda x: x.next_step,
            {
                Steps.evaluate_tools: str(Steps.evaluate_tools),
                Steps.error_handler: str(Steps.error_handler),
            },
        )
        graph.add_conditional_edges(
            str(Steps.generate_response),
            lambda x: x.next_step,
            {
                Steps.end: END,
                Steps.error_handler: str(Steps.error_handler),
            },
        )

        graph.add_conditional_edges(
            str(Steps.error_handler),
            lambda x: x.next_step,
            {
                Steps.evaluate_tools: str(Steps.evaluate_tools),
                Steps.end: END,
            },
        )

        return graph

    def _load_memory(self) -> BaseCheckpointSaver:
        uri = env.POSTGRES_URI
        if uri:
            # 1. open a long‑lived connection
            raw = connect(
                uri,
                autocommit=True,
                prepare_threshold=0,
            )
            raw.row_factory = dict_row  # type: ignore[assignment]
            conn = cast(Connection[DictRow], raw)  # 💡 silence Pyright/mypy
            saver = PostgresSaver(conn)
            saver.setup()  # one‑time DDL
            return saver

        # fallback when no PG URI
        return MemorySaver()
