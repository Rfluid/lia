import asyncio
import json
import os
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv
from websockets.client import connect

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_BASE = f"{API_URL}/agent"  # Adjust if needed
MESSAGES_URL = f"{API_BASE}/messages/user"
SYSTEM_INSTRUCTIONS_URL = f"{API_BASE}/messages/system"


def http_to_ws(url: str) -> str:
    """Convert http(s) -> ws(s) for WebSocket endpoints."""
    return url.replace("https://", "wss://").replace("http://", "ws://")


def state_url(tid):
    return f"{API_BASE}/threads/{tid}/state"


def history_url(tid):
    return f"{API_BASE}/threads/{tid}/history"


def clear_url(tid):
    return f"{API_BASE}/threads/{tid}"


WS_MESSAGES_URL = f"{http_to_ws(API_BASE)}/messages/user/websocket"

st.set_page_config(page_title="🧠 Lia AI Agent", layout="wide")

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "latest_state" not in st.session_state:
    st.session_state.latest_state = None
if "full_history" not in st.session_state:
    st.session_state.full_history = None


# Centralized function to set query parameter with key and value
def set_query_param(key, value):
    st.query_params[key] = str(value)  # Ensure values are strings for URL


# Get initial values from query parameters or set defaults
initial_thread_id = st.query_params.get("thread_id")
if initial_thread_id is None:
    initial_thread_id = "80085"
    set_query_param("thread_id", initial_thread_id)
else:
    initial_thread_id = str(initial_thread_id)

initial_max_retries = st.query_params.get("max_retries")
if initial_max_retries is None:
    initial_max_retries = 1
    set_query_param("max_retries", initial_max_retries)
else:
    initial_max_retries = int(initial_max_retries)

initial_loop_threshold = st.query_params.get("loop_threshold")
if initial_loop_threshold is None:
    initial_loop_threshold = 3
    set_query_param("loop_threshold", initial_loop_threshold)
else:
    initial_loop_threshold = int(initial_loop_threshold)

initial_top_k = st.query_params.get("top_k")
if initial_top_k is None:
    initial_top_k = 5
    set_query_param("top_k", initial_top_k)
else:
    initial_top_k = int(initial_top_k)

initial_use_ws = st.query_params.get("use_ws")
if initial_use_ws is None:
    initial_use_ws = "0"
    set_query_param("use_ws", initial_use_ws)


# Sidebar settings
with st.sidebar:
    st.title("⚙️ Settings")

    use_websocket = st.toggle(
        "Use WebSocket (streaming)",
        value=str(initial_use_ws) == "1",
        help="Stream assistant deltas over WebSocket instead of HTTP.",
    )
    set_query_param("use_ws", "1" if use_websocket else "0")

    thread_id = st.text_input(
        "Thread ID",
        value=initial_thread_id,
        on_change=lambda: set_query_param(
            "thread_id", st.session_state.thread_id_input
        ),
        key="thread_id_input",
    )
    system_instructions = st.text_area("System Instructions", height=100)

    max_retries = st.number_input(
        "Max Retries",
        min_value=0,
        step=1,
        value=initial_max_retries,
        help="How many times Lia should retry before failing.",
        on_change=lambda: set_query_param(
            "max_retries", st.session_state.max_retries_input
        ),
        key="max_retries_input",
    )
    loop_threshold = st.number_input(
        "Loop Threshold",
        min_value=1,
        step=1,
        value=initial_loop_threshold,
        help="Maximum number of times a single step can occur in the step history, preventing infinite loops.",
        on_change=lambda: set_query_param(
            "loop_threshold", st.session_state.loop_threshold_input
        ),
        key="loop_threshold_input",
    )
    top_k = st.number_input(
        "Top K",
        min_value=0,
        step=1,
        value=initial_top_k,
        help="How many top K results to return during RAG.",
        on_change=lambda: set_query_param("top_k", st.session_state.top_k_input),
        key="top_k_input",
    )

    # Send system instructions button
    if st.button("Send System Instructions"):
        payload = {
            "data": system_instructions,
            "thread_id": thread_id,
        }
        try:
            r = requests.post(SYSTEM_INSTRUCTIONS_URL, json=payload)
            r.raise_for_status()
            st.success("System instructions sent successfully.")
        except Exception as e:
            st.error(f"Error sending system instructions: {e}")

    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.session_state.latest_state = None
        st.session_state.full_history = None
        st.success("Chat reset.")

    if st.button("🔍 Latest Thread State"):
        try:
            r = requests.get(state_url(thread_id))
            r.raise_for_status()
            st.session_state.latest_state = r.json()
            st.success("Latest state loaded.")
        except Exception as e:
            st.error(f"Error loading state: {e}")

    if st.button("🕓 Full Thread History"):
        try:
            r = requests.get(history_url(thread_id))
            r.raise_for_status()
            st.session_state.full_history = r.json()
            st.success("Full history loaded.")
        except Exception as e:
            st.error(f"Error loading history: {e}")

    if st.button("🗑 Clear thread"):
        try:
            r = requests.delete(clear_url(thread_id))
            r.raise_for_status()
            st.success("Thread cleared")
        except Exception as e:
            st.error(f"Error clearing thread: {e}")


# Display chat messages
st.title("💬 Chat with Lia")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Message input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Show user message immediately
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    payload = {
        "data": user_input,
        "thread_id": thread_id,
        "max_retries": max_retries,
        "top_k": top_k,
        "loop_threshold": loop_threshold,
        "chat_interface": "websocket" if use_websocket else "api",
    }

    if not use_websocket:
        # === HTTP mode (unchanged) ===
        try:
            response = requests.post(MESSAGES_URL, json=payload)
            response.raise_for_status()
            res_json = response.json()

            assistant_reply = res_json["response"]

            with st.chat_message("assistant"):
                st.markdown(assistant_reply)

                if res_json.get("action_payloads"):
                    with st.expander("📦 Action Payloads", expanded=False):
                        st.json(res_json["action_payloads"])

            st.session_state.messages.append(
                {"role": "assistant", "content": assistant_reply}
            )

        except Exception as e:
            st.chat_message("assistant").markdown(f"⚠️ Error: {str(e)}")

    else:
        # === WebSocket streaming mode ===
        try:
            with st.chat_message("assistant"):
                stream_area = st.empty()
                accumulated: str = ""
                final_payload: dict[str, Any] | None = None

                async def run_ws():
                    local_accumulated: str = ""
                    local_final: dict[str, Any] | None = None

                    async with connect(WS_MESSAGES_URL) as ws:
                        await ws.send(json.dumps(payload))
                        while True:
                            raw = await ws.recv()
                            msg = json.loads(raw)

                            msg_type = msg.get("type")
                            data = msg.get("data") or {}

                            if msg_type == "delta":
                                # Expecting partial LLMAPIResponse shape
                                response_delta = data.get("response") or ""
                                if response_delta:
                                    local_accumulated = response_delta
                                    stream_area.markdown(local_accumulated)

                            elif msg_type == "final":
                                local_final = data
                                final_text = data.get("response") or local_accumulated
                                stream_area.markdown(final_text)

                                ap = data.get("action_payloads")
                                if ap:
                                    with st.expander(
                                        "📦 Action Payloads", expanded=False
                                    ):
                                        st.json(ap)
                                break
                            else:
                                # Unknown frame type; ignore
                                pass

                    return local_accumulated, local_final

                accumulated, final_payload = asyncio.run(run_ws())

                final_text_for_history = (
                    final_payload.get("response") if final_payload else None
                ) or accumulated
                st.session_state.messages.append(
                    {"role": "assistant", "content": final_text_for_history}
                )

        except Exception as e:
            st.chat_message("assistant").markdown(f"⚠️ WS error: {str(e)}")

# Thread State (collapsed by default)
if st.session_state.latest_state:
    with st.expander("🧠 Latest Thread State", expanded=False):
        st.json(st.session_state.latest_state)

# Thread History (top-level expanders, not nested)
if st.session_state.full_history:
    st.subheader("📜 Full Thread History")
    for i, snap in enumerate(st.session_state.full_history[::-1]):
        with st.expander(
            f"Snapshot #{len(st.session_state.full_history) - i}", expanded=False
        ):
            st.json(snap)
