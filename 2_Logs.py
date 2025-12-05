import streamlit as st

from components.layout import render_header, render_footer
from utils.session import init_state, get_logs, clear_logs

# 初始化 session_state
init_state()

# ========== 页面布局 ==========

render_header(
    title="Pantry Assistant – Logs",
    subtitle="Inspect frontend and pipeline events",
)

st.subheader("Log Controls")

col1, col2, col3 = st.columns([2, 2, 1])

logs = get_logs()

# 提取可用的过滤选项
all_roles = sorted({entry.get("role", "unknown") for entry in logs}) or ["user", "assistant"]
all_sources = sorted({entry.get("source", "unknown") for entry in logs}) or ["frontend", "pipeline"]
all_events = sorted({entry.get("event", "unknown") for entry in logs}) or ["user_message", "assistant_reply"]

with col1:
    selected_roles = st.multiselect(
        "Role",
        options=all_roles,
        default=all_roles,
    )

with col2:
    selected_sources = st.multiselect(
        "Source",
        options=all_sources,
        default=all_sources,
    )

with col3:
    st.write("")  # 对齐
    st.write("")
    if st.button("Clear logs"):
        clear_logs()
        st.success("All logs cleared.")
        logs = []  # 清空本地变量，避免下面继续显示

search_text = st.text_input("Search text (in message or raw json)", value="")

st.markdown("---")

# ========== 日志列表展示 ==========

st.subheader("Log Entries")

if not logs:
    st.info("No logs yet. Interact with the chat page to generate logs.")
else:
    # 过滤逻辑
    def match_filters(entry: dict) -> bool:
        role = entry.get("role", "unknown")
        source = entry.get("source", "unknown")
        event = entry.get("event", "unknown")
        if role not in selected_roles:
            return False
        if source not in selected_sources:
            return False
        if event not in all_events and selected_sources:
            # 对未知 event 的简单保护
            pass
        if search_text:
            raw_str = str(entry)
            if search_text.lower() not in raw_str.lower():
                return False
        return True

    filtered_logs = [e for e in logs if match_filters(e)]

    st.write(f"Showing **{len(filtered_logs)}** of **{len(logs)}** total log entries.")

    # 逐条展示
    for idx, entry in enumerate(reversed(filtered_logs), start=1):
        with st.expander(f"#{idx} - {entry.get('event', 'event')} [{entry.get('source', 'unknown')}]"):
            st.json(entry)

render_footer("Pantry Assistant © 2025")
