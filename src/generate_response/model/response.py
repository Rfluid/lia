from typing import Literal

from pydantic import BaseModel, Field

from src.generate_response.model.action_payloads import (
    ActionPayloads,
)


class BaseLLMResponse(BaseModel):
    action_payloads: ActionPayloads | None = Field(
        default=None,
        description="Payloads for the actions to be performed. This will contain the data to create, update or delete events.",
    )
    next_step: Literal["end"] = Field(
        description="""Next step to be executed after this.
This will be used to determine the next step in the workflow.
Choose `end` if you want to keep going with the chat (e. g. if you are waiting for a message from the user)."""
    )
    next_step_reason: str = Field(
        description="The reason why the agent needs to use this next step."
    )


class LLMAPIResponse(BaseLLMResponse):
    response: str = Field(description="LLM's text response to the input query.")


LLMResponse = LLMAPIResponse
