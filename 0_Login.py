import streamlit as st
import asyncio
from utils.session import init_state
from utils.async_runner import run_async

# Initialize session state keys
init_state()

st.set_page_config(page_title="Login", layout="centered")

st.title("Login to Pantry Assistant")


# -----------------------------------------
# If already authenticated → redirect tip
# -----------------------------------------
if st.session_state.get("authenticated", False):
    st.success("You are already logged in.")
    st.page_link("pages/1_Chat.py", label="Go to Chat →")
    st.stop()


# -----------------------------------------
# Sidebar navigation (only show Login)
# -----------------------------------------
st.sidebar.page_link("pages/0_Login.py", label="Login")


# -----------------------------------------
# Mock async authentication function
#
# Replace this later with async DB lookup:
#   async def verify_user_db(username, password):
#       ...
# -----------------------------------------
async def verify_user(username: str, password: str) -> bool:
    await asyncio.sleep(0.2)  # simulate async call
    # Simple mock login (replace with DB logic later)
    return username == "admin" and password == "1234"

"""
# Example for future real DB usage:

async def verify_user(username: str, password: str) -> bool:
    async for session in get_session():
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalars().first()
        if not user:
            return False
        return user.password_hash == hash(password)
"""


# -----------------------------------------
# Login Form
# -----------------------------------------
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    is_valid = run_async(verify_user(username, password))

    if is_valid:
        st.session_state["authenticated"] = True
        st.session_state["username"] = username   # ⭐ required for Authorization header
        st.success("Login successful!")
        st.page_link("pages/1_Chat.py", label="Go to Chat →")
        st.stop()
    else:
        st.error("Invalid username or password.")
