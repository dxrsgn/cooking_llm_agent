import streamlit as st

from components.layout import render_header, render_footer
from utils.session import init_state

# 全局页面配置
st.set_page_config(
    page_title="Pantry Assistant",
    layout="wide",
)

# 初始化 session_state 结构
init_state()

# 尝试检测后端 orchestrator 是否可用
try:
    from backend.agents.orchestrator import handle_user_message as _probe  # noqa: F401
    HAS_BACKEND = True
except Exception:
    HAS_BACKEND = False

# ========== 页面顶部 ==========

render_header(
    title="Pantry Assistant",
    subtitle="Async multi-agent recipe and pantry recommender",
)

col_main, col_side = st.columns([3, 1])

with col_main:
    st.markdown(
        """
        ### Welcome 👋

        This is the **frontend entry** for the Pantry Assistant project.

        Use the sidebar to navigate between:

        - **Chat** – main conversational interface with ChatGPT-style bubbles  
        - **Logs** – inspect frontend and pipeline events (for debugging and demos)

        The UI is designed to work with an **async backend pipeline**,  
        where multiple agents (clarification, retriever, critic, substitute, etc.)  
        can run concurrently.
        """
    )

with col_side:
    st.markdown("### System status")
    st.markdown(
        "- Backend: " + ("✅ connected" if HAS_BACKEND else "⚠ mock mode"),
    )
    st.markdown(
        """
        **Tips:**
        - Start with the **Chat** page to see the conversation flow.
        - Open **Logs** while chatting to observe events in real time.
        """
    )

st.markdown("---")

st.markdown(
    """
    ### How to use

    1. Open the **Chat** page from the sidebar.  
    2. Type what you would like to cook, or describe your pantry.  
    3. The frontend sends your message to the async pipeline (or mock).  
    4. Agent steps and responses are logged and can be inspected on the **Logs** page.
    """
)

render_footer("Pantry Assistant © 2025")
