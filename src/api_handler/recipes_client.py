import httpx
from src.api_handler.datamodels import Recipe, RecipeSearchQuery
import asyncio
from src.api_handler.constants import RECIPES_URL, MAX_RECIPES
from tenacity import retry, stop_after_attempt, wait_exponential
from src.api_handler.recipes_funcs import (map_mealdb_meal_to_recipe, 
                                           recipe_has_anchor, 
                                           recipe_has_excluded_ingredient, 
                                           count_include_matches)


class RecipesAPIClient:
    base_url = RECIPES_URL
    max_recipes = MAX_RECIPES

    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=10.0,
        )

    async def close(self):
        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=15))
    async def _search_by_name(self, query: str) -> list[Recipe]:
        resp = await self._client.get("/search.php", params={"s": query})
        resp.raise_for_status()
        data = resp.json()
        meals = data.get("meals") or []
        return [map_mealdb_meal_to_recipe(m) for m in meals]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=15))
    async def _search_by_ingredient(self, ingredient: str) -> list[Recipe]:
        resp = await self._client.get("/filter.php", params={"i": ingredient})
        resp.raise_for_status()
        data = resp.json()
        meals = data.get("meals") or []

        ids = [m["idMeal"] for m in meals]
        recipes: list[Recipe] = []

        for meal_id in ids[: self.max_recipes]:
            r = await self._client.get("/lookup.php", params={"i": meal_id})
            r.raise_for_status()
            meal = r.json()["meals"][0]
            recipes.append(map_mealdb_meal_to_recipe(meal))

        return recipes

    async def search(self, query: RecipeSearchQuery) -> list[Recipe]:
        if not query.is_valid():
            raise ValueError("Provide query_text or include_ingredients")

        candidates: list[Recipe] = []

        if query.query_text:
            candidates.extend(await self._search_by_name(query.query_text))

        if query.include_ingredients:
            tasks = [
                self._search_by_ingredient(i)
                for i in query.include_ingredients
            ]
            results = await asyncio.gather(*tasks)
            for part in results:
                candidates.extend(part)

        unique: dict[str, Recipe] = {}
        for r in candidates:
            unique[r.id] = r
        recipes = list(unique.values())

        exclude_set = {e.lower() for e in query.exclude_ingredients}
        if exclude_set:
            recipes = [
                r for r in recipes
                if not recipe_has_excluded_ingredient(r, exclude_set)
            ]

        include_set = {i.lower() for i in query.include_ingredients}
        anchor = query.include_ingredients[0].lower() if query.include_ingredients else None

        scored = []
        for r in recipes:
            match_count = count_include_matches(r, include_set)
            has_anchor = recipe_has_anchor(r, anchor) if anchor else True
            full_match = match_count == len(include_set)

            scored.append((r, has_anchor, full_match, match_count))

        scored.sort(
            key=lambda x: (
                not x[1],
                not x[2],
                -x[3],   
                len(x[0].ingredients),
            )
        )

        recipes = [x[0] for x in scored]

        return recipes[: self.max_recipes]
