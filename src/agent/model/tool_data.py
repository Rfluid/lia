from typing import Any
from pydantic import BaseModel


class ToolData(BaseModel):
    data: Any  # Must be serializable
    label: str  # Describe the data here

    def __str__(self) -> str:
        return f"{self.label}: {self.data}"
