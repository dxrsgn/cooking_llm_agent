import os
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from src.agent.graph import build_graph
from src.agent.models import UserProfile
from src.agent.states import AgentState
from src.api_handler.recipes_client import RecipesAPIClient
from phoenix.otel import register
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from openinference.instrumentation.langchain import LangChainInstrumentor

load_dotenv()


tracer_provider = register(
    project_name="aboba",
    auto_instrument=False,
)
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
HTTPXClientInstrumentor().instrument()
tracer = tracer_provider.get_tracer("aboba")

app = FastAPI()

checkpointer = MemorySaver()
graph = build_graph(checkpointer=checkpointer)

recipes_client = RecipesAPIClient()


class GraphRequest(BaseModel):
    thread_id: str
    message: str | None = None


class GraphResponse(BaseModel):
    message: str
    thread_id: str


@app.post("/graph", response_model=GraphResponse)
async def call_graph(
    request: GraphRequest,
    authorization: str = Header(..., alias="Authorization")
):
    try:
        config = {
            "configurable": {
                "thread_id": request.thread_id,
                "model_name": os.getenv("LLM_MODEL_NAME", "gpt-4o-mini"),
                "llm_api_key": os.getenv("LLM_API_KEY"),
                "llm_api_url": os.getenv("LLM_API_URL"),
                "reasoning": os.getenv("LLM_REASONING", "false").lower() == "true",
                "recipes_client": recipes_client
            }
        }

        if not request.message:
            raise HTTPException(status_code=400, detail="Message is required")

        try:
            state_snapshot = await checkpointer.aget(config)  # type: ignore
            if state_snapshot and state_snapshot.values and state_snapshot.values.get("__interrupt__"):  # type: ignore
                result = await graph.ainvoke(Command(resume=request.message), config=config)  # type: ignore
            else:
                state = AgentState(
                    messages=[HumanMessage(content=request.message)],
                    user_profile=UserProfile()
                )
                result = await graph.ainvoke(state, config=config)  # type: ignore
        except Exception:
            state = AgentState(
                messages=[HumanMessage(content=request.message)],
                user_profile=UserProfile()
            )
            result = await graph.ainvoke(state, config=config)  # type: ignore

        if "__interrupt__" in result and result["__interrupt__"]:
            interrupt_info = result["__interrupt__"][0]
            return GraphResponse(
                message=interrupt_info.value,
                thread_id=request.thread_id
            )

        if result.get("messages") and len(result["messages"]) > 0:
            last_message = result["messages"][-1]
            message_content = last_message.content if hasattr(last_message, "content") else str(last_message)
            return GraphResponse(
                message=message_content,
                thread_id=request.thread_id
            )
        else:
            return GraphResponse(
                message="No message available",
                thread_id=request.thread_id
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    await recipes_client.close()


def main():
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
