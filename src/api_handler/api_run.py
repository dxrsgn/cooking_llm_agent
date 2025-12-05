
import asyncio

from src.api_handler.recipes_client import RecipesAPIClient
from src.api_handler.nutrition_client import NutritionAPIClient
from src.api_handler.nutrition_funcs import enrich_recipes_with_nutrition
from src.api_handler.datamodels import RecipeSearchQuery


async def api_run(include_ingredients: list[str] = ["chicken", "honey"],
                  exclude_ingredients: list[str] = ["mushroom"]):
    meal_client = RecipesAPIClient()
    nutrition_client = NutritionAPIClient()

    query = RecipeSearchQuery(
        include_ingredients=include_ingredients,
        exclude_ingredients=exclude_ingredients
    )
    recipes = await meal_client.search(query)
    print(f"Found {len(recipes)} recipes")

    enriched_recipes = await enrich_recipes_with_nutrition(recipes, nutrition_client)

    for r in enriched_recipes[:3]:
        print(f"Recipe: {r.title}")
        for ing in r.ingredients:
            print(f"  {ing.name} — {ing.amount} — Calories: {ing.calories_per100g}")

    await meal_client.close()
    await nutrition_client.close()

    return  enriched_recipes


def main():
    asyncio.run(api_run())


if __name__ == "__main__":
    main()