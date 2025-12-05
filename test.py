import subprocess
import time
import requests
import sys
import os
from pathlib import Path



FRONTEND_DIR = Path("/Users/duanran/Personal/study/Industry_ML")
APP_FILE = FRONTEND_DIR / "app.py"
SERVER_URL = "http://localhost:8501"


def wait_for_streamlit(timeout=20):
    """
    等待 streamlit 服务器启动。
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            r = requests.get(SERVER_URL)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def test_page(path: str):
    """
    访问指定页面并检查是否正常访问。
    """
    url = f"{SERVER_URL}{path}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            print(f"[OK] Page {path} loaded.")
            return True
        else:
            print(f"[FAIL] Page {path} returned code {r.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to load page {path}: {e}")
        return False


def main():
    # -----------------------------
    # 1. 启动 Streamlit
    # -----------------------------
    print("Starting Streamlit server...")

    if not APP_FILE.exists():
        print(f"ERROR: Cannot find {APP_FILE}, please check path.")
        sys.exit(1)

    # 启动 streamlit 作为子进程
    process = subprocess.Popen(
        ["streamlit", "run", str(APP_FILE), "--server.headless=true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(FRONTEND_DIR),
    )

    print("Waiting for server to become available...")
    time.sleep(2)

    # -----------------------------
    # 2. 等待服务器启动
    # -----------------------------
    if not wait_for_streamlit():
        print("[FAIL] Streamlit failed to start.")
        process.kill()
        sys.exit(1)

    print("[OK] Streamlit is running.\n")

    # -----------------------------
    # 3. 测试主页
    # -----------------------------
    home_ok = test_page("/")
    chat_ok = test_page("/Chat")
    logs_ok = test_page("/Logs")

    # -----------------------------
    # 4. 清理子进程
    # -----------------------------
    print("\nStopping Streamlit server...")
    process.kill()

    print("\n===== Test Summary =====")
    print(f"Home Page: {'OK' if home_ok else 'FAIL'}")
    print(f"Chat Page: {'OK' if chat_ok else 'FAIL'}")
    print(f"Logs Page: {'OK' if logs_ok else 'FAIL'}")

    if all([home_ok, chat_ok, logs_ok]):
        print("\n All frontend tests passed!")
    else:
        print("\n Some tests failed. Check logs above.")


if __name__ == "__main__":
    main()
