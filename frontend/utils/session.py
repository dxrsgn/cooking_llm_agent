# utils/session.py

from typing import List, Tuple, Dict, Any
import streamlit as st

# --- 初始化 ---------------------------------------------------------------

def init_state():
    """
    初始化 session_state 中需要用到的键。
    在每个页面文件开头调用一次即可：
        from utils.session import init_state
        init_state()
    """
    if "chat_history" not in st.session_state:
        st.session_state.chat_history: List[Tuple[str, str]] = []

    if "logs" not in st.session_state:
        st.session_state.logs: List[Dict[str, Any]] = []


# --- 聊天记录相关 ---------------------------------------------------------

def get_chat_history() -> List[Tuple[str, str]]:
    """
    获取当前聊天记录。
    返回格式: List[(role, message)]
        role: "user" 或 "assistant"
        message: 文本内容（可以是 markdown）
    """
    return st.session_state.chat_history


def add_chat_message(role: str, message: str) -> None:
    """
    向聊天记录中追加一条消息。

    :param role: "user" 或 "assistant"
    :param message: 消息文本
    """
    st.session_state.chat_history.append((role, message))


def clear_chat_history() -> None:
    """清空聊天记录。"""
    st.session_state.chat_history = []


# --- 日志相关 -------------------------------------------------------------

def get_logs() -> List[Dict[str, Any]]:
    """
    获取当前日志列表。
    每一项建议是一个 dict，如:
        {
            "agent": "retriever",
            "step": "vector_db_search",
            "payload": {...}
        }
    """
    return st.session_state.logs


def add_log_entry(entry: Dict[str, Any]) -> None:
    """
    追加一条日志记录。

    :param entry: 日志字典，内容结构由你自己约定
    """
    st.session_state.logs.append(entry)


def clear_logs() -> None:
    """清空所有日志。"""
    st.session_state.logs = []
