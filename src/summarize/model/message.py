from langchain_core.messages import BaseMessage


class SummaryMessage(BaseMessage):
    """Special message type to represent a summarization of past history."""

    type: str = "summary"
    # metadata: dict | None
