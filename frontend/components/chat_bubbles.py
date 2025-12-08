# components/chat_bubbles.py

import streamlit as st

# --- HTML 模板定义 ---------------------------------------------------------

USER_BUBBLE_HTML = """
<div style="
    display: flex;
    justify-content: flex-end;
    margin: 10px 0;
">
    <div style="
        background: #DCF8C6;
        padding: 10px 14px;
        border-radius: 12px;
        max-width: 70%;
        font-size: 16px;
        line-height: 1.5;
        color: #000000;
    ">
        {msg}
    </div>
</div>
"""

ASSISTANT_BUBBLE_HTML = """
<div style="
    display: flex;
    justify-content: flex-start;
    margin: 10px 0;
">
    <div style="
        background: #F1F0F0;
        padding: 10px 14px;
        border-radius: 12px;
        max-width: 70%;
        font-size: 16px;
        line-height: 1.5;
        color: #000000;
    ">
        {msg}
    </div>
</div>
"""


# --- 渲染函数 --------------------------------------------------------------

def render_user_msg(msg: str):
    """渲染用户气泡"""
    st.markdown(USER_BUBBLE_HTML.format(msg=msg), unsafe_allow_html=True)


def render_assistant_msg(msg: str):
    """渲染助手气泡"""
    st.markdown(ASSISTANT_BUBBLE_HTML.format(msg=msg), unsafe_allow_html=True)
