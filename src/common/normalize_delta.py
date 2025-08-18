from typing import Any

from pydantic import BaseModel


def normalize_delta(delta: Any) -> dict[str, Any]:
    # Turn whatever the chain yields into a dict we can JSON-encode
    if isinstance(delta, BaseModel):
        return delta.model_dump()
    if isinstance(delta, dict):
        return delta
    if delta | (bytes, bytearray):
        return {"text": delta.decode("utf-8", errors="replace")}
    # strings, numbers, etc.
    return {"text": str(delta)}
