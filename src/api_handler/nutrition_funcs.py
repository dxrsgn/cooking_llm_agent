import asyncio

from src.api_handler.datamodels import Recipe
from src.api_handler.nutrition_client import NutritionAPIClient


async def enrich_recipes_with_nutrition(
    recipes: list[Recipe],
    nutrition_client: NutritionAPIClient,
) -> list[Recipe]:
    all_ingredients = set()
    for recipe in recipes:
        for ingredient in recipe.ingredients:
            all_ingredients.add(nutrition_client.normalize_name(ingredient.name))

    nutrition_results = await asyncio.gather(
        *[nutrition_client.get_nutrition(ing) for ing in all_ingredients]
    )
    nutrition_map = dict(zip(all_ingredients, nutrition_results))

    for recipe in recipes:
        for ingredient in recipe.ingredients:
            norm_name = nutrition_client.normalize_name(ingredient.name)
            nutrition_info = nutrition_map.get(norm_name)
            if nutrition_info:
                ingredient.calories_per100g = nutrition_info.get("calories_per_100g")
    return recipes
