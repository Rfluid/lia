from typing import Annotated, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field

from src.agent.model.chat_interface import ChatInterface
from src.agent.model.steps import Steps
from src.agent.model.tool_payloads import ToolPayloads


class GraphState(BaseModel):
    input: list[BaseMessage]
    response: BaseMessage | None = None

    messages: Annotated[list[BaseMessage], add_messages] = []
    chat_interface: ChatInterface = ChatInterface.api

    next_step: Steps | None = None
    step_history: list[Steps] = Field(default_factory=list)
    loop_threshold: int = 3

    tool_payloads: ToolPayloads = ToolPayloads()

    function: Literal["context_incrementer", "response_generator"] = Field(
        default="response_generator",
        description="The function to be executed by the graph. `response_generator` will generate a response and `context_incrementer` will increment the context.",
    )

    error: str | None = None
    current_retries: int = 0
    max_retries: int = 0

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

    top_k: int = Field(
        # default=5,
        description="The number of top k results to return.",
    )
