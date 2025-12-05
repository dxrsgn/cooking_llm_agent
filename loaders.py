# components/loaders.py

import streamlit as st
import time

THINKING_HTML = """
<div style="
    font-size: 16px;
    color: #888888;
    padding: 6px 0;
">
    <em>Assistant is thinking… ⌛</em>
</div>
"""


def show_thinking():
    """
    显示“正在思考”提示，返回 placeholder 供后续清除。
    """
    placeholder = st.empty()
    placeholder.markdown(THINKING_HTML, unsafe_allow_html=True)
    return placeholder


def clear_thinking(placeholder):
    """
    清除前一步生成的“thinking...”占位。
    """
    placeholder.empty()
