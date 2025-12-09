from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from psycopg import AsyncConnection
from psycopg.rows import dict_row, DictRow
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from phoenix.otel import register
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from openinference.instrumentation.langchain import LangChainInstrumentor

from redis.asyncio import Redis

from backend.config import POSTGRES_URI, REDIS_URL
from backend.schemas import GraphRequest, GraphResponse, LoginRequest, LoginResponse
from backend.dependencies import app_state
from backend.services import (
    build_graph_config,
    build_user_profile,
    invoke_graph,
    extract_response_message,
)
from src.agent.graph import build_graph
from src.database.crud import init_db, get_session, get_user_by_login, get_profile_by_user_id, update_profile
from src.api_handler.recipes_client import RecipesAPIClient
from src.api_handler.nutrition_client import NutritionAPIClient

tracer_provider = register(project_name="aboba", auto_instrument=False)
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
HTTPXClientInstrumentor().instrument()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_state.pool = AsyncConnectionPool(conninfo=POSTGRES_URI, kwargs={"autocommit": True, "row_factory": dict_row})
    await app_state.pool.open()
    app_state.checkpointer = AsyncPostgresSaver(app_state.pool)
    await app_state.checkpointer.setup()
    app_state.graph = build_graph(checkpointer=app_state.checkpointer)
    app_state.redis = Redis.from_url(REDIS_URL)
    app_state.recipes_client = RecipesAPIClient(redis=app_state.redis)
    app_state.nutrition_client = NutritionAPIClient(redis=app_state.redis)
    yield
    await app_state.redis.close()
    await app_state.recipes_client.close()
    await app_state.nutrition_client.close()
    await app_state.pool.close()


app = FastAPI(lifespan=lifespan)
init_db()


@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    with get_session() as session:
        user = get_user_by_login(session, request.username)
        if user is not None and str(user.password) == request.password:
            return LoginResponse(success=True, message="Login successful")
        return LoginResponse(success=False, message="Invalid username or password")


@app.post("/graph", response_model=GraphResponse)
async def call_graph(
    request: GraphRequest,
    authorization: str = Header(..., alias="Authorization")
):
    if app_state.checkpointer is None or app_state.graph is None:
        raise HTTPException(status_code=503, detail="Service is not ready")
    
    if not request.message:
        raise HTTPException(status_code=400, detail="Message is required")

    user_id = None
    db_profile = None
    # get profile from database
    if authorization:
        with get_session() as session:
            user = get_user_by_login(session, authorization)
            if user is not None:
                user_id = user.id
                db_profile = get_profile_by_user_id(session, user_id)

    config = build_graph_config(request.thread_id)
    user_profile = build_user_profile(db_profile)

    try:
        result = await invoke_graph(request.message, user_profile, config)
        
        if user_id is not None and "__interrupt__" not in result:
            with get_session() as session:
                update_profile(session, user_id, last_queries=result["user_profile"].last_queries)

        return GraphResponse(
            message=extract_response_message(result),
            thread_id=request.thread_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
