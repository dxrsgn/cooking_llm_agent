from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import DictRow
from redis.asyncio import Redis

from src.api_handler.recipes_client import RecipesAPIClient
from src.api_handler.nutrition_client import NutritionAPIClient
from langgraph.graph.state import CompiledStateGraph


class AppState:
    pool: AsyncConnectionPool[AsyncConnection[DictRow]] | None = None
    checkpointer: AsyncPostgresSaver | None = None
    graph: CompiledStateGraph | None = None
    recipes_client: RecipesAPIClient | None = None
    nutrition_client: NutritionAPIClient | None = None
    redis: Redis | None = None


app_state = AppState()

