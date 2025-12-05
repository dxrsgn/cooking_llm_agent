from typing import Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from .models import UserProfile, UserRecipeQuery
from src.api_handler.datamodels import Recipe


class AgentState(BaseModel):
    messages: Annotated[list, add_messages]
    user_profile: UserProfile = UserProfile()
    user_recipe_query: UserRecipeQuery | None = None
    recipes: list[Recipe] = []

class RecipeSearchState(BaseModel):
    messages: Annotated[list, add_messages]
    recipes: list[Recipe] = []