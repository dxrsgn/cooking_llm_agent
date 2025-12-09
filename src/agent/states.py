from typing import Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from .schemas.objects import UserProfile
from .schemas.structured_output import UserRecipeQuery, ClarificationDecision, RecipeSelection
from src.api_handler.datamodels import Recipe


def add_unique_recipes(existing: list[Recipe], new: list[Recipe]) -> list[Recipe]:
    seen_ids = {r.id for r in existing}
    return existing + [r for r in new if r.id not in seen_ids]


class AgentState(BaseModel):
    messages: Annotated[list, add_messages]
    user_profile: UserProfile = UserProfile()
    user_recipe_query: UserRecipeQuery | None = None
    selected_recipes: list[Recipe] = []

class RecipeSearchSubgraphState(BaseModel):
    iterations: int = 0
    user_recipe_query: UserRecipeQuery
    messages: Annotated[list, add_messages]
    current_recipes: list[Recipe] = []
    selected_recipes: Annotated[list[Recipe], add_unique_recipes] = []
    recipe_selection: RecipeSelection | None = None