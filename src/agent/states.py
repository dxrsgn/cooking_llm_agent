from operator import add
from typing import Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from .schemas.objects import UserProfile
from .schemas.structured_output import UserRecipeQuery, ClarificationDecision, RecipeSelection
from src.api_handler.datamodels import Recipe


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
    # add reducer to accumulate selected recipes
    selected_recipes: Annotated[list[Recipe], add] = []
    recipe_selection: RecipeSelection | None = None