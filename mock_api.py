from fastapi import FastAPI, Header
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    thread_id: str

class ChatResponse(BaseModel):
    message: str
    thread_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, Authorization: str = Header(default=None)):
    # Here Authorization = username
    # You can store thread_id mapping later if needed

    return ChatResponse(
        message=f"Mock reply to: {payload.message} (user={Authorization})",
        thread_id=payload.thread_id
    )

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=9000)
