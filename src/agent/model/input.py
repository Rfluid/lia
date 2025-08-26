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

    summarize_message_window: int = Field(
        default=4,
        description="""Number of messages to summarize at once (the "window"),
        taken from the block immediately before the KEEP tail. Summarization triggers
        ONLY when the window is FULL (i.e., len(messages) >= SUMMARIZE_MESSAGE_KEEP + SUMMARIZE_MESSAGE_WINDOW).""",
    )
    summarize_message_keep: int = Field(
        default=6,
        description="""Number of most recent messages to always keep verbatim (the "keep tail").
        Must be a non-negative integer. These messages are never summarized.""",
    )
    summarize_system_messages: bool = Field(
        default=False,
        description="""Whether system messages will enter the summarize.
If False, this will lead to a summarized history like
[system instruction messages, summary, keep messages].""",
    )


class InputRequest(Input):
    thread_id: str = Field(
        description="The ID of the thread to which this message belongs.",
    )
