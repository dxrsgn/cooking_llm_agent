from pydantic import BaseModel, Field
from typing import Literal


class UserRecipeQuery(BaseModel):
    """Schema for structured recipe query with user preferences and restrictions"""
    query: str = Field(description="The user's summarized recipe query or request")
    preferences: list[str] = Field(default=[], description="List of user's dietary preferences")
    restrictions: list[str] = Field(default=[], description="List of dietary restrictions or allergies")


class ClarificationDecision(BaseModel):
    """Schema for clarification decision"""
    ask_more_questions: Literal["yes", "no"] = Field(
        ...,
        description="yes if you need to ask more questions to the user, no if you have enough information to generate the schema"
    )
    question: str = Field(default="", description="The question to ask the user if ask_more_questions is True")


class RecipeSelection(BaseModel):
    """Schema for recipe selection by critic agent"""
    selected_recipe_ids: list[str] = Field(
        ...,
        description="List of recipe IDs that meet the user's query requirements"
    )
    reason: str = Field(
        ...,
        description="Short summary of the reason for the selection of the recipe IDs"
    )