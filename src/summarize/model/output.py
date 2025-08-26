from pydantic.fields import Field
from pydantic.main import BaseModel


class SummarizeOutput(BaseModel):
    summary: str = Field(description="Summary of the conversation.")
