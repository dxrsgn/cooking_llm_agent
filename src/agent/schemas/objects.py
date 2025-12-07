from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    last_queries: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
