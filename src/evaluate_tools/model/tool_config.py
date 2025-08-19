from typing import Any, Literal

from pydantic import BaseModel, Field

from src.generate_response.model.response import LLMAPIResponse, WebSocketData


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
    # reason: str = Field(description="The reason why the agent needs to use this tool.")


class ToolConfigWithResponse(LLMAPIResponse):
    rag_query: str | None = Field(
        default=None,
        description="The query to be sent to the RAG tool. Used to retrieve information from the RAG tool.",
    )
    tool: Literal["rag", "end"] = Field(
        description="The tool that the agent needs to use to retrieve the necessary information or send message back do user (`end`)."
    )


class ToolConfigWebSocketResponse(BaseModel):
    type: WebSocketData = Field(description="Data type.")
    data: Any = Field(
        description="Data returned by the model. Can be a delta or the full response."
    )
