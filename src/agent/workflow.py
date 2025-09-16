import logging
from collections import Counter
from collections.abc import Hashable
from typing import cast

from fastapi import HTTPException
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row

from src.agent.model.chat_interface import ChatInterface
from src.agent.model.graph_state import GraphState
from src.agent.model.steps import Steps
from src.agent.model.tool_data import ToolData
from src.config import env
from src.config.env.llm import PARALLEL_GENERATION
from src.config.env.vector import RAG_AVAILABLE
from src.error_handler import ErrorHandler
from src.evaluate_tools.main import EvaluateTools
from src.evaluate_tools.model.tool_config import (
    ToolConfig,
    ToolConfigWithResponse,
)
from src.generate_response import ResponseGenerator
from src.summarize.main import Summarizer
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
    compiled_graph: CompiledStateGraph | None
    memory: BaseCheckpointSaver | None
    vector_manager: VectorManager
    summarizer: Summarizer

    def __init__(self) -> None:
        super().__init__()
        self.tool_evaluator = EvaluateTools()
        self.response_generator = ResponseGenerator()
        self.vector_manager = VectorManager()
        self.error_handler = ErrorHandler()
        self.summarizer = Summarizer()

        self.graph = self._load_graph()
        self.memory = None
        self.compiled_graph = None
        self._db_conn: AsyncConnection[DictRow] | None = (
            None  # keep to close later if you want
        )

    async def ensure_ready(self) -> None:
        """Idempotent: prepares memory + compiles graph once."""
        if self.compiled_graph is not None:
            return
        self.memory = await self._load_memory()
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

    async def generate_summary(
        self,
        state: GraphState,
        config: RunnableConfig | None = None,
    ) -> GraphState:
        state.step_history.append(Steps.summarize)

        if config is None:
            raise ValueError("Graph config unavailable.")

        try:
            self.summarizer.summarize_conditionally(state, config)
        except Exception as e:
            state.error = str(e)
            state.next_step = Steps.error_handler

        return state

    async def generate_response(
        self,
        state: GraphState,
        config: RunnableConfig | None = None,
    ) -> GraphState:
        state.step_history.append(Steps.generate_response)

        if config is None:
            raise ValueError("Graph config unavailable.")

        try:
            match state.chat_interface:
                case ChatInterface.api:
                    response = self.response_generator.generate_response(
                        config,
                        state.messages,
                    )
                case ChatInterface.websocket:
                    # Retrieve websocket from the config you passed earlier
                    websocket = config.get("configurable", {}).get("websocket")

                    if websocket is None:
                        raise ValueError("No WebSocket for WebSocket chat interface.")

                    response = (
                        await self.response_generator.generate_websocket_response(
                            websocket,
                            config,
                            state.messages,
                        )
                    )
                # case ChatInterface.whatsapp:
                #     response = self.response_generator.generate_whatsapp_response(
                #         self.compiled_graph.config,
                #         state.messages,
                #     )

            state.next_step = Steps.end  # Steps(response.next_step)

            ai_message = AIMessage(content=[response.model_dump()])
            state.response = ai_message
            state.messages = [ai_message]
        except Exception as e:
            state.error = str(e)
            state.next_step = Steps.error_handler

        return state

    async def decide_next_step(
        self,
        state: GraphState,
        config: RunnableConfig | None = None,
    ) -> GraphState:
        state.step_history.append(Steps.evaluate_tools)

        if config is None:
            raise ValueError("Graph config unavailable.")

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

            match state.chat_interface:
                case ChatInterface.api:
                    response = self.tool_evaluator.decide_next_step(
                        config,
                        state.messages,
                    )
                case ChatInterface.websocket:
                    # Retrieve websocket from the config you passed earlier
                    websocket = config.get("configurable", {}).get("websocket")

                    if websocket is None:
                        raise ValueError("No WebSocket for WebSocket chat interface.")

                    response = await self.tool_evaluator.stream_next_step_via_websocket(
                        websocket,
                        config,
                        state.messages,
                    )

            if isinstance(response, ToolConfigWithResponse):
                ai_message = AIMessage(content=[response.model_dump()])
                state.messages = [ai_message]
                if response.tool == "end":
                    state.response = ai_message
            else:
                reasoning = BaseMessage(
                    type="reasoning", content=[response.model_dump()]
                )
                state.messages = [reasoning]

            state.next_step = Steps(response.tool)

            if isinstance(response, ToolConfig) or isinstance(
                response, ToolConfigWithResponse
            ):
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

            # Retrieve relevant documents from the vectorstore
            retrieved_docs = self.vector_manager.retrieve(
                query=query, top_k=state.top_k
            )

            # Create a new rag_data message with the retrieved documents
            documents_message = BaseMessage(
                content=[
                    str(
                        ToolData(
                            data=retrieved_docs,
                            label=f"Knowledge base documents retrieved for: '{query}'",
                        )
                    )
                ],
                type="rag_data",
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
        if state.error is None:
            raise ValueError("No error to handle.")

        if state.current_retries >= state.max_retries:
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
        graph.add_node(str(Steps.summarize), self.generate_summary)
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

        # Setting conditionally the `evaluate_tools` edges considering the parallel runtime
        evaluate_tools_edges: dict[Hashable, str] = {
            Steps.error_handler: str(Steps.error_handler),
        }
        if env.RAG_AVAILABLE:
            rag: Hashable = Steps.rag
            evaluate_tools_edges[rag] = str(Steps.rag)
        if not PARALLEL_GENERATION:
            # Generate the response possibly in the next step
            generate_response: Hashable = Steps.generate_response
            evaluate_tools_edges[generate_response] = str(Steps.generate_response)
        else:
            # Generate the response with the tool decision
            end: Hashable = Steps.end
            evaluate_tools_edges[end] = str(Steps.summarize)
        graph.add_conditional_edges(
            str(Steps.evaluate_tools),
            lambda x: x.next_step,
            evaluate_tools_edges,
        )

        if RAG_AVAILABLE:
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
                Steps.end: str(Steps.summarize),
                Steps.error_handler: str(Steps.error_handler),
            },
        )
        graph.add_edge(str(Steps.summarize), END)

        graph.add_conditional_edges(
            str(Steps.error_handler),
            lambda x: x.next_step,
            {
                Steps.evaluate_tools: str(Steps.evaluate_tools),
                Steps.end: END,
            },
        )

        return graph

    async def _load_memory(self) -> BaseCheckpointSaver:
        uri = env.POSTGRES_URI
        if uri:
            conn = await AsyncConnection.connect(
                uri,
                autocommit=True,
                prepare_threshold=0,
            )
            conn.row_factory = dict_row  # type: ignore[assignment]
            self._db_conn = cast(AsyncConnection[DictRow], conn)

            saver = AsyncPostgresSaver(self._db_conn)
            await saver.setup()  # one-time DDL
            return saver

        # fallback when no PG URI
        return MemorySaver()
