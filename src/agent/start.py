from typing import Literal

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig

from src.agent.model.chat_interface import ChatInterface
from src.agent.model.graph_state import GraphState
from src.agent.workflow import Workflow

workflow = Workflow()


async def start(
    input: list[BaseMessage],
    config: RunnableConfig,
    function: Literal[
        "context_incrementer", "response_generator"
    ] = "response_generator",
    chat_interface: ChatInterface = ChatInterface.api,
    max_retries: int = 1,
    loop_threshold: int = 3,
    top_k: int = 5,
):
    """
    Start the agent with the given input.
    """
    await workflow.ensure_ready()
    assert workflow.compiled_graph is not None

    initial_state = GraphState(
        input=input,
        function=function,
        chat_interface=chat_interface,
        max_retries=max_retries,
        loop_threshold=loop_threshold,
        top_k=top_k,
    )

    result = await workflow.compiled_graph.ainvoke(initial_state.model_dump(), config)

    return result
