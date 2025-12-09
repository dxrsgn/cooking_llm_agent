from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import DictRow

from src.api_handler.recipes_client import RecipesAPIClient
from langgraph.graph.state import CompiledStateGraph


class AppState:
    pool: AsyncConnectionPool[AsyncConnection[DictRow]] | None = None
    checkpointer: AsyncPostgresSaver | None = None
    graph: CompiledStateGraph | None = None
    recipes_client: RecipesAPIClient | None = None


app_state = AppState()

