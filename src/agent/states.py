from typing import Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from .models import UserProfile, UserRecipeQuery


class AgentState(BaseModel):
    messages: Annotated[list, add_messages]
    user_profile: UserProfile = UserProfile()
    final_query: UserRecipeQuery | None = None

