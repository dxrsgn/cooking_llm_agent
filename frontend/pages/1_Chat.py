import asyncio
import uuid
import httpx
import streamlit as st

from components.chat_bubbles import render_user_msg, render_assistant_msg
from components.loaders import show_thinking, clear_thinking
from components.layout import render_header, render_footer
from utils.async_runner import run_async
from utils.session import (
    init_state,
    get_chat_history,
    add_chat_message,
    add_log_entry,
    clear_chat_history,
)

# ========== Authentication Check ==========
if not st.session_state.get("authenticated", False):
    st.error("You must log in first.")
    st.page_link("pages/0_Login.py", label="Go to Login")
    st.stop()

# Load username (for Authorization header)
username = st.session_state.get("username", "anonymous")

# Initialize session state keys
init_state()

# Ensure thread_id exists for this user session
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())

thread_id = st.session_state["thread_id"]


# ========== Mock API HTTP Call (Async) ==========
async def send_to_backend(message: str):
    payload = {
        "message": message,
        "thread_id": thread_id,
    }

    headers = {
        "Authorization": username
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://backend:8000/chat",   # mock API endpoint
            json=payload,
            headers=headers,
            timeout=15.0
        )
        resp.raise_for_status()
        return resp.json()   # expected: {"message": str, "thread_id": str}


# ========== Page Layout ==========

render_header(
    title="Pantry Assistant – Chat",
    subtitle="ChatGPT-style interface for recipe and pantry planning",
)

col_left, col_right = st.columns([4, 1])

with col_right:
    st.subheader("Controls")

    if st.button("Clear chat history"):
        clear_chat_history()
        st.success("Chat history cleared.")

    st.markdown(" ")
    st.markdown("**Status**")
    st.markdown("- Backend: POST /chat (mock API)")
    st.markdown(f"- User: **{username}**")
    st.markdown(f"- Thread ID: `{thread_id}`")

with col_left:
    st.subheader("Conversation")


# ========== Display Chat History ==========

chat_history = get_chat_history()

chat_container = st.container()
with chat_container:
    for role, message in chat_history:
        if role == "user":
            render_user_msg(message)
        else:
            render_assistant_msg(message)


# ========== User Input Handling ==========

user_input = st.chat_input("What would you like to cook today?")

if user_input:
    # Save user message
    add_chat_message("user", user_input)
    add_log_entry(
        {
            "role": "user",
            "message": user_input,
            "source": "frontend",
            "event": "user_message",
        }
    )

    # Render user bubble immediately
    with chat_container:
        render_user_msg(user_input)

    # Show thinking indicator
    thinking_placeholder = show_thinking()

    # Call mock API asynchronously
    async def _call_api():
        return await send_to_backend(user_input)

    response_json = run_async(_call_api())
    assistant_reply = response_json["message"]

    # Remove thinking indicator
    clear_thinking(thinking_placeholder)

    # Save assistant message
    add_chat_message("assistant", assistant_reply)
    add_log_entry(
        {
            "role": "assistant",
            "message": assistant_reply,
            "source": "mock_api",
            "event": "assistant_reply",
        }
    )

    # Render assistant bubble
    with chat_container:
        render_assistant_msg(assistant_reply)


render_footer("Pantry Assistant © 2025")
