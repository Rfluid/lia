import logging
import os
import uuid
from datetime import datetime
from typing import Annotated, Literal, cast

import pytest
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from psycopg import Connection, connect
from psycopg.rows import DictRow, dict_row
from pydantic import Field
from pydantic.main import BaseModel

from src.agent import start
from src.agent.model.chat_interface import ChatInterface
from src.config import env
from src.llm.service import load_model

# ---------- Logging (stdlib only) ----------
logger = logging.getLogger(__name__)


# ---------- Helpers ----------
def _role_name(msg: BaseMessage) -> str:
    if isinstance(msg, SystemMessage):
        return "system"
    if isinstance(msg, HumanMessage):
        return "user"
    if isinstance(msg, AIMessage):
        return "assistant"
    return getattr(msg, "type", "message")


def _content_text(msg: BaseMessage) -> str:
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content
    # Handle LC list-of-parts content
    parts = []
    try:
        for c in content:
            if isinstance(c, dict):
                if "text" in c:
                    parts.append(c["text"])
                elif "type" in c:
                    parts.append(f"[{c['type']}]")
                else:
                    parts.append(str(c))
            else:
                parts.append(str(c))
        return "\n".join(parts)
    except Exception:
        return str(content)


def _print_banner(title: str) -> None:
    line = "-" * max(10, 70 - len(title))
    logger.info(f"\n=== {title} {line}")


def _print_end() -> None:
    logger.info("=" * 84 + "\n")


def _print_message(msg: BaseMessage, turn: int, who: str) -> None:
    role = _role_name(msg)
    ts = datetime.now().strftime("%H:%M:%S")
    header = f"{who.upper()} -> ({role}) @ {ts} | turn {turn}"
    logger.info(header)
    text = _content_text(msg).strip() or "∅"
    logger.info(text + "\n")


def _maybe_log_meta(prefix: str, msg: BaseMessage) -> None:
    meta = getattr(msg, "response_metadata", None)
    if not isinstance(meta, dict):
        return
    # provider-dependent; best-effort
    usage = meta.get("usage") or meta.get("token_usage")
    tool_calls = meta.get("tool_calls") or meta.get("tool_calls_delta")
    if usage:
        logger.debug(f"{prefix} usage: {usage}")
    if tool_calls:
        logger.debug(f"{prefix} tool_calls: {tool_calls}")


# ---------- Utilities ----------
def _load_memory() -> BaseCheckpointSaver:
    uri = env.POSTGRES_URI
    if uri:
        # 1. open a long‑lived connection
        raw = connect(
            uri,
            autocommit=True,
            prepare_threshold=0,
        )
        raw.row_factory = dict_row  # type: ignore[assignment]
        conn = cast(Connection[DictRow], raw)  # 💡 silence Pyright/mypy
        saver = PostgresSaver(conn)
        saver.setup()  # one‑time DDL
        return saver

    # fallback when no PG URI
    return MemorySaver()


def _load_prompt() -> str:
    prompts_dir = env.PROMPTS_DIR
    primary_path = prompts_dir / "user.md"
    fallback_path = prompts_dir / "user.example.md"

    if primary_path.is_file():
        return primary_path.read_text(encoding="utf-8")
    elif fallback_path.is_file():
        return fallback_path.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(f"Neither {primary_path} nor {fallback_path} found.")


# ---------- Graph state for simulated user ----------
class UserGraphState(BaseModel):
    input: BaseMessage = Field(description="The input passed to the LLM.")
    messages: Annotated[list[BaseMessage], add_messages] = []


# ---------- Simulated user LLM ----------
def _load_model():
    logger.info("Setting up the LLM that will simulate the user")
    model = load_model(
        env.TEST_LLM_PROVIDER,
        env.TEST_LLM_MODEL_NAME,
        env.TEST_LLM_API_KEY,
        model_stop=env.TEST_LLM_STOP,
        model_temperature=env.TEST_LLM_TEMPERATURE,
    )
    return model


model = _load_model()


def _generate_response(
    state: UserGraphState, config: RunnableConfig | None = None
) -> UserGraphState:
    response = model.invoke(state.messages, config)
    assert isinstance(response, BaseMessage)
    state.messages = [response]
    return state


def _context_builder(state: UserGraphState) -> UserGraphState:
    if not state.messages or len(state.messages) == 0:
        prompt = _load_prompt()
        agent_context = SystemMessage(content=prompt)
        state.messages = [agent_context]
        state.input = agent_context
    else:
        state.messages = [state.input]
    return state


# ---------- LangGraph user sim setup ----------
def _setup_user_graph() -> CompiledStateGraph:
    logger.info("Setting up the langgraph that will mock the user")
    memory = _load_memory()

    context_builder = "context_builder"
    generate_response = "generate_response"

    graph = StateGraph(UserGraphState)
    graph.add_node(context_builder, _context_builder)
    graph.add_node(generate_response, _generate_response)

    graph.set_entry_point(context_builder)
    graph.add_edge(context_builder, generate_response)
    graph.add_edge(generate_response, END)

    return graph.compile(checkpointer=memory)


compiled_user_graph = _setup_user_graph()


# ---------- Options ----------
function: Literal["context_incrementer", "response_generator"] = "response_generator"
chat_interface = ChatInterface.api
max_retries: int = 1
loop_threshold: int = 3
top_k: int = 5

# Default to 10 if not provided in environment
messages_sent = int(os.getenv("MESSAGES_SENT", 10))


# ---------- Test entry ----------
@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ["asyncio"], indirect=True)
async def test_start_real_workflow():
    """
    LLM A simulates the user; your main agent runs via `start`.
    Logs a readable transcript for each turn using stdlib logging only.
    """
    logger.info("🧪 Starting workflow test")

    # stable threads for the whole run
    user_thread_id = f"user-{uuid.uuid4()}"
    ai_thread_id = f"agent-{uuid.uuid4()}"

    user_config: RunnableConfig = {"configurable": {"thread_id": user_thread_id}}
    ai_config: RunnableConfig = {"configurable": {"thread_id": ai_thread_id}}

    # seed the simulated user
    seed_to_user = HumanMessage("Generate the first message to be sent to the AI.")
    user_state = UserGraphState(input=seed_to_user)

    transcript: list[BaseMessage] = []

    _print_banner("Conversation Begins")

    for turn in range(1, messages_sent + 1):
        try:
            # --- Simulated User turn ---
            user_resp_state = compiled_user_graph.invoke(user_state, user_config)
            user_msg: BaseMessage = user_resp_state["messages"][-1]
            transcript.append(user_msg)
            _print_message(user_msg, turn, who="user")
            _maybe_log_meta("User", user_msg)

            # --- Main Agent turn ---
            ai_input: list[BaseMessage] = [
                HumanMessage(content=_content_text(user_msg))
            ]
            ai_raw = await start(
                ai_input,
                ai_config,
                function,
                chat_interface,
                max_retries,
                loop_threshold,
            )

            ai_text: str = ai_raw["response"].content[-1]["response"]

            agent_msg = AIMessage(ai_text)
            transcript.append(agent_msg)
            _print_message(agent_msg, turn, who="agent")
            _maybe_log_meta("Agent", agent_msg)

            # prepare next user step with the agent reply as context
            user_state = UserGraphState(input=agent_msg)

        except Exception as e:
            logger.exception(f"❌ Error on turn {turn}: {e}")
            break

    _print_end()
    assert transcript, "Conversation produced no messages."
