from langchain_core.runnables import RunnableConfig
from langgraph.pregel.types import StateSnapshot

from src.agent import workflow


async def get_thread_history(thread_id: str) -> list[StateSnapshot]:
    """
    Retrieve the full execution history of a specific thread.
    """

    await workflow.ensure_ready()
    assert workflow.compiled_graph is not None

    config = RunnableConfig(configurable={"thread_id": thread_id})
    history = []
    async for snap in workflow.compiled_graph.aget_state_history(config):
        history.append(snap)
    return history


async def get_latest_thread_state(thread_id: str) -> StateSnapshot:
    """
    Retrieve the latest state of a specific thread.
    """
    await workflow.ensure_ready()
    assert workflow.compiled_graph is not None

    config = RunnableConfig(configurable={"thread_id": thread_id})
    latest_state = await workflow.compiled_graph.aget_state(config)
    return latest_state


async def clear_thread(thread_id: str) -> None:
    """
    Clear the state and history of a specific thread.

    Raises:
        RuntimeError: If the thread could not be cleared.
    """
    try:
        await workflow.ensure_ready()
        assert workflow.compiled_graph is not None

        config = RunnableConfig(configurable={"thread_id": thread_id})
        workflow.compiled_graph.update_state(config=config, values=None)
    except Exception as e:
        raise RuntimeError(f"Could not clear thread {thread_id}") from e
