import asyncio
import httpx
import uuid
import subprocess

BASE = "http://localhost:8000"   # 本地测试 (docker 映射)
BACKEND_CONTAINER = "cooking_llm_agent-backend-1"


async def test_login():
    print("\n=== Test 1: Login API ===")
    payload = {"username": "user1", "password": "password1"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE}/login", json=payload)

        print("Status:", resp.status_code)
        print("Response:", resp.text)

        if resp.status_code == 200:
            data = resp.json()
            print("Success:", data.get("success"))
        return resp.status_code == 200


async def test_graph_missing_auth():
    print("\n=== Test 2: Call /graph without Authorization (Expect 422) ===")

    payload = {"thread_id": "test123", "message": "Hello"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE}/graph", json=payload)

        print("Status:", resp.status_code)
        print("Response:", resp.text)


async def test_graph_with_auth():
    print("\n=== Test 3: Call /graph with Authorization (Expect 200) ===")

    payload = {
        "thread_id": str(uuid.uuid4()),
        "message": "Hello from test script!"
    }

    headers = {
        "Authorization": "admin"  # 必须与数据库用户一致
    }

    async with httpx.AsyncClient(timeout=60.0) as client:  # 60 秒避免超时
        resp = await client.post(
            f"{BASE}/graph",
            json=payload,
            headers=headers
        )

        print("Status:", resp.status_code)
        print("Response:", resp.text)

        if resp.status_code == 200:
            print("Graph result:", resp.json())


def test_backend_logs():
    print("\n=== Test 4: Fetching Backend Logs (tail 200) ===")
    try:
        output = subprocess.check_output(
            ["docker", "compose", "logs", "backend", "--tail=200"],
            text=True
        )
        print(output)
    except Exception as e:
        print(f"Error reading logs: {e}")


def test_graph_curl():
    print("\n=== Test 5: Simulate cURL call to /graph ===")
    payload = '{"thread_id":"test123","message":"hello"}'
    try:
        output = subprocess.check_output(
            [
                "curl", "-X", "POST",
                f"{BASE}/graph",
                "-H", "Content-Type: application/json",
                "-H", "Authorization: admin",
                "-d", payload
            ],
            text=True
        )
        print(output)
    except subprocess.CalledProcessError as e:
        print("curl error:", e.output)


async def main():
    print("==== Running Backend API Tests ====\n")

    await test_login()
    await test_graph_missing_auth()
    await test_graph_with_auth()

    test_backend_logs()   # 新增：自动抓 backend logs
    test_graph_curl()     # 新增：自动模拟 curl 请求

    print("\n==== Tests Completed ====\n")


if __name__ == "__main__":
    asyncio.run(main())
