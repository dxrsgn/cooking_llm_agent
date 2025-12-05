from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    last_queries: list[str] = []
    preferences: list[str] = []
    allergies: list[str] = []


class UserRecipeQuery(BaseModel):
    """Schema for structured recipe query with user preferences and restrictions"""
    query: str = Field(description="The user's summarized recipe query or request")
    preferences: list[str] = Field(default=[], description="List of user's dietary preferences")
    restrictions: list[str] = Field(default=[], description="List of dietary restrictions or allergies")


class ClarificationDecision(BaseModel):
    """Schema for clarification decision"""
    ask_more_questions: bool = Field(
        ...,
        description="True if you need to ask more questions to the user, False if you have enough information to generate the schema"
    )
    question: str = Field(default="", description="The question to ask the user if ask_more_questions is True")
