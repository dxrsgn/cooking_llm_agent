from pydantic import BaseModel


class IngredientRequirement(BaseModel):
    name: str
    amount: None | str = None
    calories_per100g: None | float = None


class Recipe(BaseModel):
    id: str
    title: str
    ingredients: list[IngredientRequirement]
    instructions: None | str = None


class RecipeSearchQuery(BaseModel):
    query_text: None | str = None
    include_ingredients: list[str] = []
    exclude_ingredients: list[str] = []

    def is_valid(self) -> bool:
        return bool(self.query_text or self.include_ingredients)
