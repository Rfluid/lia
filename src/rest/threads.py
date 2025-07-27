from fastapi import APIRouter, HTTPException

from src.agent.threads import clear_thread, get_latest_thread_state, get_thread_history

router = APIRouter()


@router.get("/{thread_id}/state")
async def get_thread_state_endpoint(thread_id: str):
    """
    API endpoint to retrieve the latest state of a specific thread.
    """
    try:
        state_snapshot = get_latest_thread_state(thread_id)
        return {
            "values": state_snapshot.values,
            "metadata": state_snapshot.metadata,
            "created_at": state_snapshot.created_at,
            "checkpoint_id": state_snapshot.config.get("configurable", {}).get(
                "checkpoint_id"
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Could not retrieve thread state: {e}"
        ) from e


@router.get("/{thread_id}/history")
async def get_thread_history_endpoint(thread_id: str):
    """
    API endpoint to retrieve the full execution history of a specific thread.
    """
    try:
        history = get_thread_history(thread_id)
        return [
            {
                "values": snapshot.values,
                "metadata": snapshot.metadata,
                "created_at": snapshot.created_at,
                "checkpoint_id": snapshot.config.get("configurable", {}).get(
                    "checkpoint_id"
                ),
            }
            for snapshot in history
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Could not retrieve thread history: {e}"
        ) from e


@router.delete("/{thread_id}")
async def delete_thread_data(thread_id: str):
    try:
        clear_thread(thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not clear thread: {e}") from e
