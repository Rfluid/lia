import logging

from fastapi import (
    APIRouter,
    HTTPException,
)
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.agent import start
from src.agent.model import Input
from src.agent.model.graph_state import GraphState
from src.agent.model.input import InputRequest
from src.generate_response.model.response import LLMResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/user", response_model=LLMResponse)
async def send_chat_message(
    req: InputRequest,
):
    try:
        config: RunnableConfig = {"configurable": {"thread_id": req.thread_id}}
        input: list[BaseMessage] = [
            HumanMessage(
                content=[
                    Input.model_validate(
                        {
                            "data": req.data,
                        }
                    ).model_dump()
                ]
            ),
        ]

        agent_response = start(
            input,
            config,
            "response_generator",
            req.chat_interface,
            req.max_retries,
            req.loop_threshold,
            req.top_k,
        )

        message = agent_response["response"]

        return message.content[0]
    except Exception as e:
        logger.error(f"Error sending chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Could not send chat message: {e}"
        ) from e


@router.post("/system", response_model=GraphState)
async def send_system_instructions(
    req: InputRequest,
):
    try:
        config: RunnableConfig = {"configurable": {"thread_id": req.thread_id}}
        input: list[BaseMessage] = [
            SystemMessage(
                content=[
                    Input.model_validate(
                        {
                            "data": req.data,
                        }
                    ).model_dump()
                ]
            ),
        ]

        agent_response = start(
            input,
            config,
            "context_incrementer",
            req.chat_interface,
            req.top_k,
        )

        return agent_response
    except Exception as e:
        logger.error(f"Error sending system instructions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Could not send system instructions: {e}"
        ) from e
