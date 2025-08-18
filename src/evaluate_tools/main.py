import os
from typing import Any

from fastapi import WebSocket
from langchain.llms.base import BaseLLM
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableSerializable

from src.common import normalize_delta
from src.config import env
from src.config.env.llm import PARALLEL_GENERATION
from src.evaluate_tools.model import ToolConfig
from src.evaluate_tools.model.tool_config import (
    ToolConfigWebSocketResponse,
    ToolConfigWithResponse,
)
from src.generate_response.model.response import WebSocketData
from src.llm.service import load_model


class EvaluateTools:
    model: BaseLLM | BaseChatModel
    prompt: str
    chain: RunnableSerializable
    output_class = ToolConfig

    def __init__(self):
        self.model = load_model(
            env.TOOL_EVALUATOR_LLM_PROVIDER,
            env.TOOL_EVALUATOR_LLM_MODEL_NAME,
            env.TOOL_EVALUATOR_LLM_API_KEY,
            model_stop=env.TOOL_EVALUATOR_LLM_STOP,
            model_temperature=env.TOOL_EVALUATOR_LLM_TEMPERATURE,
        )
        self.prompt = self._load_prompt()
        self.chain = self._load_chain()
        if PARALLEL_GENERATION:
            self.output_class = ToolConfigWithResponse

    def decide_next_step(
        self,
        config: RunnableConfig | None = None,
        query: list | None = None,
    ) -> ToolConfig | ToolConfigWithResponse:
        response = self.chain.invoke(
            {
                "query": query,
            },
            config=config,
        )

        return self.output_class.model_validate(response)

    async def stream_next_step_via_websocket(
        self,
        websocket: WebSocket,
        config: RunnableConfig | None = None,
        query: list | None = None,
    ) -> ToolConfig | ToolConfigWithResponse:
        """
        Streams LLM response deltas and final message via websocket.
        """

        # Accumulate a sensible "final" shape; adjust keys as your client expects
        final_data: dict[str, Any] = {"response": ""}

        # Stream deltas
        async for delta in self.chain.astream({"query": query}, config=config):
            payload = normalize_delta(delta)

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
            json_dump = ToolConfigWebSocketResponse(
                type=WebSocketData.delta, data=payload
            ).model_dump(mode="json")
            await websocket.send_json(json_dump)

        # Send the final frame with the accumulated data
        final_msg = ToolConfigWebSocketResponse(
            type=WebSocketData.final, data=final_data
        )
        await websocket.send_json(final_msg.model_dump(mode="json"))

        # Return an API response validated from the final accumulated data
        return ToolConfigWithResponse.model_validate(final_data)

    def _load_prompt(self) -> str:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        prompt_dir = os.path.join(root_dir, "prompts")
        primary_path = os.path.join(prompt_dir, "evaluate_tools.md")
        fallback_path = os.path.join(prompt_dir, "evaluate_tools.example.md")

        if os.path.isfile(primary_path):
            with open(primary_path, encoding="utf-8") as f:
                return f.read()
        elif os.path.isfile(fallback_path):
            with open(fallback_path, encoding="utf-8") as f:
                return f.read()
        else:
            raise FileNotFoundError(
                "Neither prompts/evaluate_tools.md nor prompts/evaluate_tools.example.md found."
            )

    def _load_chain(self):
        parser = JsonOutputParser(pydantic_object=self.output_class)
        prompt = PromptTemplate(
            template=f"{self.prompt}",
            input_variables=[
                "query",
            ],
            output_parser=parser,
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        chain = prompt | self.model | parser
        return chain
