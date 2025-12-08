import os
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from langgraph.types import Command
from src.agent.graph import build_graph
from src.agent.schemas.objects import UserProfile
from src.agent.states import AgentState
from src.database.crud import init_db, get_session, get_user_by_login, get_profile_by_user_id, update_profile
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

pool: AsyncConnectionPool | None = None
checkpointer: AsyncPostgresSaver | None = None
graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool, checkpointer, graph
    db_uri = os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/langgraph")
    pool = AsyncConnectionPool(conninfo=db_uri, kwargs={"autocommit": True})
    await pool.open()
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    graph = build_graph(checkpointer=checkpointer)
    yield
    await pool.close()


app = FastAPI(lifespan=lifespan)

recipes_client = RecipesAPIClient()

init_db()

class GraphRequest(BaseModel):
    thread_id: str
    message: str | None = None


class GraphResponse(BaseModel):
    message: str
    thread_id: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str


@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    with get_session() as session:
        user = get_user_by_login(session, request.username)
        if user and user.password == request.password:
            return LoginResponse(success=True, message="Login successful")
        return LoginResponse(success=False, message="Invalid username or password")


@app.post("/graph", response_model=GraphResponse)
async def call_graph(
    request: GraphRequest,
    authorization: str = Header(..., alias="Authorization")
):
    user_profile = None
    user_id = None
    if authorization:
        with get_session() as session:
            user = get_user_by_login(session, authorization)
            if user:
                user_id = user.id
                user_profile = get_profile_by_user_id(session, user_id)

    if checkpointer is None or graph is None:
        raise HTTPException(status_code=503, detail="Service is not ready")
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

        agent_profile = UserProfile()
        if user_profile:
            agent_profile = UserProfile(
                last_queries=list(user_profile.last_queries or []),
                preferences=list(user_profile.preferences or []),
                allergies=list(user_profile.allergies or [])
            )

        try:
            state_snapshot = await checkpointer.aget(config)  # type: ignore
            if state_snapshot and state_snapshot.values and state_snapshot.values.get("__interrupt__"):  # type: ignore
                result = await graph.ainvoke(Command(resume=request.message), config=config)  # type: ignore
            else:
                state = AgentState(
                    messages=[HumanMessage(content=request.message)],
                    user_profile=agent_profile
                )
                result = await graph.ainvoke(state, config=config)  # type: ignore
                if user_id is not None:
                    with get_session() as session:
                        update_profile(session, user_id, last_queries=result["user_profile"].last_queries)
        except Exception:
            state = AgentState(
                messages=[HumanMessage(content=request.message)],
                user_profile=agent_profile
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
    if pool:
        await pool.close()


def main():
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
