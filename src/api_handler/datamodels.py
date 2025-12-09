from pydantic import BaseModel, RootModel


class IngredientRequirement(BaseModel):
    name: str
    amount: None | str = None
    calories_per100g: None | float = None


class Recipe(BaseModel):
    id: str
    title: str
    ingredients: list[IngredientRequirement]
    instructions: None | str = None
    total_calories: None | float = None


class RecipeSearchQuery(BaseModel):
    query_text: None | str = None
    include_ingredients: list[str] = []
    exclude_ingredients: list[str] = []
    area: None | str = None

    def is_valid(self) -> bool:
        return bool(self.query_text or self.include_ingredients or self.area)


class RecipeCalories(BaseModel):
    id: str
    total_calories: int


class CaloriesResponse(RootModel):
    root: list[RecipeCalories]
