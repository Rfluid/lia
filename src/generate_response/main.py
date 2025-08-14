import logging
from typing import Any

from fastapi.websockets import WebSocket
from langchain.llms.base import BaseLLM
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableSerializable
from pydantic import BaseModel

from src.config import env
from src.generate_response.model.response import (
    LLMAPIResponse,
    LLMWebSocketResponse,
    WebSocketData,
)
from src.llm.service import load_model

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,  # or DEBUG
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class ResponseGenerator:
    model: BaseLLM | BaseChatModel
    chain: RunnableSerializable
    whatsapp_chain: RunnableSerializable

    def __init__(self):
        self.model = load_model(
            env.LLM_PROVIDER,
            env.LLM_MODEL_NAME,
            env.LLM_API_KEY,
            model_stop=env.LLM_STOP,
            model_temperature=env.LLM_TEMPERATURE,
        )
        self.chain = self._load_chain()

    def generate_response(
        self,
        # data: Any,
        config: RunnableConfig | None = None,
        query: list | None = None,
    ) -> LLMAPIResponse:
        response = self.chain.invoke(
            {
                "query": query,
            },
            config=config,
        )
        return LLMAPIResponse.model_validate(response)

    async def generate_websocket_response(
        self,
        websocket: WebSocket,
        config: RunnableConfig | None = None,
        query: list | None = None,
    ) -> LLMAPIResponse:
        """
        Streams LLM response deltas and final message via websocket.
        """

        # Accumulate a sensible "final" shape; adjust keys as your client expects
        final_data: dict[str, Any] = {"response": ""}

        # Stream deltas
        async for delta in self.chain.astream({"query": query}, config=config):
            payload = _normalize_delta(delta)

            # Merge text if present; otherwise just include the latest fields
            txt = payload.get("text")
            if isinstance(txt, str):
                final_data["response"] = txt
            else:
                # Non-text fields—up to you how to merge; here we keep latest
                for k, v in payload.items():
                    if k != "text":
                        final_data[k] = v

            # Send the delta frame as JSON (DICT) — not a JSON string
            json_dump = LLMWebSocketResponse(
                type=WebSocketData.delta, data=payload
            ).model_dump(mode="json")
            await websocket.send_json(json_dump)

        # Send the final frame with the accumulated data
        final_msg = LLMWebSocketResponse(type=WebSocketData.final, data=final_data)
        await websocket.send_json(final_msg.model_dump(mode="json"))

        # Return an API response validated from the final accumulated data
        return LLMAPIResponse.model_validate(final_data)

    def _load_chain(self):
        parser = JsonOutputParser(pydantic_object=LLMAPIResponse)
        prompt = PromptTemplate(
            template="""Based on the chat history
{query}
generate a response to the user considering the data retrieved from the tools.

{format_instructions}""",
            input_variables=[
                "query",
                # "data",
            ],
            output_parser=parser,
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        chain = prompt | self.model | parser
        return chain


def _normalize_delta(delta: Any) -> dict[str, Any]:
    # Turn whatever the chain yields into a dict we can JSON-encode
    if isinstance(delta, BaseModel):
        return delta.model_dump()
    if isinstance(delta, dict):
        return delta
    if delta | (bytes, bytearray):
        return {"text": delta.decode("utf-8", errors="replace")}
    # strings, numbers, etc.
    return {"text": str(delta)}
