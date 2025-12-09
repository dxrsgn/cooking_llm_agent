from pydantic import BaseModel, Field
from typing import Literal


class UserRecipeQuery(BaseModel):
    """Schema for structured recipe query with user preferences and restrictions"""
    query: str = Field(description="The user's summarized recipe query or request")
    preferences: list[str] = Field(default=[], description="List of user's dietary preferences")
    restrictions: list[str] = Field(default=[], description="List of dietary restrictions or allergies")


class ClarificationDecision(BaseModel):
    """Schema for clarification decision"""
    continue_conversation: Literal["yes", "no"] = Field(
        ...,
        description="'yes' to stay in conversation (ask clarifying questions, respond to off-topic, handle non-recipe queries), 'no' to proceed to recipe search"
    )
    response: str = Field(default="", description="Your response or question to the user if continue_conversation is 'yes'")


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