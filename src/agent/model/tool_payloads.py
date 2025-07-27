from pydantic import BaseModel


class ToolPayloads(BaseModel):
    rag_query: str | None = None
