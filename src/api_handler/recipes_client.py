import httpx
import asyncio
from redis.asyncio import Redis
from tenacity import retry, stop_after_attempt, wait_exponential

from src.api_handler.datamodels import Recipe, RecipeSearchQuery
from src.api_handler.constants import RECIPES_URL, MAX_RECIPES, BATCH_SIZE
from src.api_handler.cache import redis_cache
from src.api_handler.recipes_funcs import (map_mealdb_meal_to_recipe, 
                                           recipe_has_anchor, 
                                           recipe_has_excluded_ingredient, 
                                           count_include_matches)


class RecipesAPIClient:
    base_url = RECIPES_URL
    max_recipes = MAX_RECIPES
    batch_size = BATCH_SIZE
    _lookup_delay = 0.3

    def __init__(self, redis: Redis | None = None):
        self._redis = redis
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=10.0,
        )

    async def close(self):
        await self._client.aclose()

    @redis_cache(prefix="recipes:lookup", ttl=3600)
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def _lookup_by_id(self, meal_id: str) -> dict | None:
        r = await self._client.get("/lookup.php", params={"i": meal_id})
        r.raise_for_status()
        meals = r.json().get("meals")
        if meals:
            return map_mealdb_meal_to_recipe(meals[0]).model_dump()
        return None

    @redis_cache(prefix="recipes:name", ttl=3600)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=8, max=15))
    async def _search_by_name(self, query: str) -> list[dict]:
        resp = await self._client.get("/search.php", params={"s": query})
        resp.raise_for_status()
        data = resp.json()
        meals = data.get("meals") or []
        return [map_mealdb_meal_to_recipe(m).model_dump() for m in meals]

    @redis_cache(prefix="recipes:ingredient", ttl=3600)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=8, max=15))
    async def _search_by_ingredient(self, ingredient: str) -> list[dict]:
        resp = await self._client.get("/filter.php", params={"i": ingredient})
        resp.raise_for_status()
        data = resp.json()
        meals = data.get("meals") or []

        ids = [m["idMeal"] for m in meals]
        recipes: list[dict] = []

        for meal_id in ids[: self.max_recipes]:
            recipe = await self._lookup_by_id(meal_id)
            if recipe:
                recipes.append(recipe)
            await asyncio.sleep(self._lookup_delay)

        return recipes

    @redis_cache(prefix="recipes:area", ttl=3600)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=8, max=15))
    async def _search_by_area(self, area: str) -> list[dict]:
        resp = await self._client.get("/filter.php", params={"a": area})
        resp.raise_for_status()
        data = resp.json()
        meals = data.get("meals") or []

        ids = [m["idMeal"] for m in meals]
        recipes: list[dict] = []

        for meal_id in ids[: self.max_recipes]:
            recipe = await self._lookup_by_id(meal_id)
            if recipe:
                recipes.append(recipe)
            await asyncio.sleep(self._lookup_delay)

        return recipes

    def _to_recipes(self, dicts: list[dict]) -> list[Recipe]:
        return [Recipe(**d) for d in dicts]

    async def search(self, query: RecipeSearchQuery) -> list[Recipe]:
        if not query.is_valid():
            raise ValueError("Provide query_text, include_ingredients, or area")

        candidates: list[Recipe] = []

        if query.query_text:
            candidates.extend(self._to_recipes(await self._search_by_name(query.query_text)))

        if query.area:
            candidates.extend(self._to_recipes(await self._search_by_area(query.area)))

        if query.include_ingredients:
            batch_size = self.batch_size
            for i in range(0, len(query.include_ingredients), batch_size):
                batch = query.include_ingredients[i:i + batch_size]
                tasks = [self._search_by_ingredient(ing) for ing in batch]
                results = await asyncio.gather(*tasks)
                for part in results:
                    candidates.extend(self._to_recipes(part))

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
