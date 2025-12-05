from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from typing import List
from pydantic import BaseModel, Field, model_validator
from src.api_handler.datamodels import Recipe, RecipeSearchQuery


class SearchRecipesByNameInput(BaseModel):
    query: str = Field(
        ...,
        description=(
            "The exact name or title to search for.  "
            "Must be a real dish name, not a common name or variation. "
            "E.g. ['Arrabiata', 'Lasagna', 'Shawarma bread'] are valid dish names. "
            "E.g. ['Italian food', 'Asian cuisine'] are not valid dish names."
        ),
        examples=[["Arrabiata", "Lasagna", "Shawarma bread"]]
    )


class SearchRecipesByIngredientInput(BaseModel):
    ingredient_exclude: list[str] | None = Field(
        description=(
            "List of ingredient names to exclude from search results. " 
            "Must be real ingredient names, not common names or variations. "
            "E.g. ['vegetarian', 'high protein'] are not valid ingredient names."
        ),
        default=None,
        examples=[["chicken", "beef", "pork", "fish"]]
    )
    ingredient_include: list[str] = Field(
        ...,
        description=(
            "List of ingredient names that must be included in recipes. "
            "At least one ingredient must be provided. "
            "Maximum of 10 ingredients can be provided. "
            "Must be real ingredient names, not common names or variations. "
            "E.g. ['vegetarian', 'high protein'] are not valid ingredient names."
        ),
        min_length=1,
        max_length=10,
        examples=[["chicken", "beef", "pork", "fish"]]
    )

    @model_validator(mode="after")
    def check_ingredient_include(self) -> "SearchRecipesByIngredientInput":
        if self.ingredient_exclude and len(self.ingredient_exclude) > 0:
            remaining_ingredients = [i for i in self.ingredient_include if i not in self.ingredient_exclude]
            if len(remaining_ingredients) == 0:
                raise ValueError(
                    "No ingredients left to search for. "
                    "At least one ingredient must be provided. "
                )
            self.ingredient_include = remaining_ingredients
        return self

class RecipeSearchResult(BaseModel):
    recipes: list[Recipe] = Field(description="List of recipes matching the search criteria")

@tool(
    args_schema=SearchRecipesByNameInput,
    description="Search for recipes by name or title"
)
async def search_recipes_by_name(
    query: str,
    config: RunnableConfig,
) -> dict:
    client = config.get("configurable", {}).get("recipes_client")
    if not client:
        raise ValueError("recipes_client not found in config")
    recipes = await client.search(RecipeSearchQuery(query_text=query))
    result = RecipeSearchResult(recipes=recipes)
    return result.model_dump()


@tool(
    args_schema=SearchRecipesByIngredientInput,
    description="Search for recipes that contain a specific ingredient"
)
async def search_recipes_by_ingredient(
    ingredient_include: list[str],
    config: RunnableConfig,
    ingredient_exclude: list[str] | None = None,
) -> dict:
    print(f"Searching for recipes with ingredients: {ingredient_include} and excluding ingredients: {ingredient_exclude}")
    client = config.get("configurable", {}).get("recipes_client")
    if not client:
        raise ValueError("recipes_client not found in config")
    recipes = await client.search(RecipeSearchQuery(
        include_ingredients=ingredient_include,
        exclude_ingredients=ingredient_exclude or []
    ))
    result = RecipeSearchResult(recipes=recipes)
    return result.model_dump()
