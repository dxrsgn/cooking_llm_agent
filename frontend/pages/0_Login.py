import streamlit as st
import asyncio
import httpx

from utils.session import init_state


BACKEND_URL = "http://backend:8000"   # Docker 内访问 backend
# 如果你本地运行，不走 docker，则用：
# BACKEND_URL = "http://localhost:8000"


st.set_page_config(page_title="Login", layout="centered")
init_state()

st.title("🔐 Login to Pantry Assistant")

# Already logged in
if st.session_state.get("authenticated", False):
    st.success(f"You are already logged in as **{st.session_state['username']}**.")
    st.page_link("pages/1_Chat.py", label="➡ Go to Chat")
    st.stop()


# -------------------------
# Async login via backend
# -------------------------
async def verify_user(username: str, password: str) -> bool:
    """Call backend /login API."""
    payload = {"username": username, "password": password}

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BACKEND_URL}/login", json=payload)
        if resp.status_code != 200:
            return False

        data = resp.json()
        return data.get("success", False)


# -------------------------
# Login Form
# -------------------------
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if not username or not password:
        st.error("Please enter both username and password.")
        st.stop()

    is_valid = asyncio.run(verify_user(username, password))

    if is_valid:
        st.session_state["authenticated"] = True
        st.session_state["username"] = username

        st.success(" Login successful!")
        st.page_link("pages/1_Chat.py", label="➡ Go to Chat")
        st.stop()

    else:
        st.error("Invalid username or password.")


# Sidebar
st.sidebar.page_link("pages/0_Login.py", label="Login")
