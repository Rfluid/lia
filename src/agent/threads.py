
from collections.abc import Iterator

from langchain_core.runnables import RunnableConfig
from langgraph.pregel.types import StateSnapshot

from src.agent import workflow


def get_thread_history(thread_id: str) -> Iterator[StateSnapshot]:
    """
    Retrieve the full execution history of a specific thread.
    """
    config = RunnableConfig(configurable={"thread_id": thread_id})
    history = workflow.compiled_graph.get_state_history(config)
    return history


def get_latest_thread_state(thread_id: str) -> StateSnapshot:
    """
    Retrieve the latest state of a specific thread.
    """
    config = RunnableConfig(configurable={"thread_id": thread_id})
    latest_state = workflow.compiled_graph.get_state(config)
    return latest_state


def clear_thread(thread_id: str) -> None:
    """
    Clear the state and history of a specific thread.

    Raises:
        RuntimeError: If the thread could not be cleared.
    """
    try:
        config = RunnableConfig(configurable={"thread_id": thread_id})
        workflow.compiled_graph.update_state(config=config, values=None)
    except Exception as e:
        raise RuntimeError(f"Could not clear thread {thread_id}") from e
