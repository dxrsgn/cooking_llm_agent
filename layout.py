# components/layout.py

import streamlit as st

def render_header(title: str, subtitle: str = ""):
    """
    页面顶部统一样式：标题 + 副标题
    """
    st.markdown(
        f"""
        <div style='padding: 10px 0;'>
            <h1 style='margin-bottom: 0;'>{title}</h1>
            <p style='color: #555; margin-top: 4px;'>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")


def render_footer(text: str = "Pantry Assistant © 2025"):
    """
    页面底部统一样式
    """
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; color: #999; padding: 10px 0; font-size: 14px;'>
            {text}
        </div>
        """,
        unsafe_allow_html=True
    )
