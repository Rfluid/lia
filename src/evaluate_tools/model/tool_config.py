from typing import Literal

from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    rag_query: str | None = Field(
        default=None,
        description="The query to be sent to the RAG tool. Used to retrieve information from the RAG tool.",
    )
    tool: Literal[
        "rag",
        "generate_response",
    ] = Field(
        description="The tool that the agent needs to use to retrieve the necessary information."
    )
    reason: str = Field(description="The reason why the agent needs to use this tool.")
