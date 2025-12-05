import asyncio

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

# 尝试导入真实 orchestrator；如果没有则使用 mock
try:
    from backend.agents.orchestrator import handle_user_message as pipeline_handle_user_message
    HAS_BACKEND = True
except Exception:
    HAS_BACKEND = False

    async def pipeline_handle_user_message(user_text: str) -> str:
        # 简单 mock，方便前端先跑起来
        await asyncio.sleep(1.0)
        return f"Mock response for: **{user_text}**\n\n(Replace me with real agent pipeline.)"


# 初始化 session_state
init_state()


# ========== 页面布局 ==========

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
    st.markdown(
        "- Backend: " + ("✅ connected" if HAS_BACKEND else "⚠ mock mode"),
    )

with col_left:
    st.subheader("Conversation")


# ========== 显示历史聊天记录 ==========

chat_history = get_chat_history()

chat_container = st.container()
with chat_container:
    for role, message in chat_history:
        if role == "user":
            render_user_msg(message)
        else:
            render_assistant_msg(message)


# ========== 处理用户输入 ==========

user_input = st.chat_input("What would you like to cook today?")

if user_input:
    # 记录用户消息
    add_chat_message("user", user_input)
    add_log_entry(
        {
            "role": "user",
            "message": user_input,
            "source": "frontend",
            "event": "user_message",
        }
    )

    # 重新渲染用户消息
    with chat_container:
        render_user_msg(user_input)

    # 显示“思考中”提示
    thinking_placeholder = show_thinking()

    # 调用异步 pipeline
    async def _run_pipeline():
        return await pipeline_handle_user_message(user_input)

    assistant_reply = run_async(_run_pipeline())

    # 清除“思考中”
    clear_thinking(thinking_placeholder)

    # 保存助手消息
    add_chat_message("assistant", assistant_reply)
    add_log_entry(
        {
            "role": "assistant",
            "message": assistant_reply,
            "source": "pipeline",
            "event": "assistant_reply",
        }
    )

    # 显示助手回复
    with chat_container:
        render_assistant_msg(assistant_reply)


render_footer("Pantry Assistant © 2025")
