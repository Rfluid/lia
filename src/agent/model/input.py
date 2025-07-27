from typing import Any

from pydantic import BaseModel, Field

from src.agent.model.chat_interface import ChatInterface


class Input(BaseModel):
    data: str | dict[str, Any] = Field(description="Input data from the user.")
    chat_interface: ChatInterface = Field(
        default=ChatInterface.api,
        description="Chat interface through which the input was received.",
    )

    # Error handling
    max_retries: int = Field(
        default=1, description="Maximum number of retries for the input."
    )

    loop_threshold: int = Field(
        default=3,
        description=(
            "The maximum number of times any individual step is allowed to appear in the "
            "step history. This helps prevent infinite loops by detecting repetitive sequences."
        ),
    )

    top_k: int = Field(default=5, description="The number of top k results to return.")


class InputRequest(Input):
    thread_id: str = Field(
        description="The ID of the thread to which this message belongs.",
    )
