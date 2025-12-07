# utils/async_runner.py

import asyncio
from typing import Any, Awaitable


def run_async(coro: Awaitable[Any]) -> Any:
    """
    统一的异步执行入口。
    在前端（Streamlit 页面）中调用异步 pipeline 时使用：
        result = run_async(handle_user_message(...))

    :param coro: 任意 async 协程对象，例如 handle_user_message(user_text)
    :return: 协程的返回值
    """
    return asyncio.run(coro)
