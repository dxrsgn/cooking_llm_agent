import re
import httpx
from async_lru import alru_cache

from src.api_handler.constants import NUTRITION_URL


class NutritionAPIClient:
    base_url = NUTRITION_URL

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=10)

    async def close(self):
        await self._client.aclose()

    @staticmethod
    def normalize_name(name: str) -> str:
        name = name.lower()
        name = re.sub(r"[^\w\s]", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name

    @alru_cache(maxsize=128)
    async def get_nutrition(self, ingredient_name: str) -> None | dict:
        params = {
            "search_terms": ingredient_name,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 5,
        }
        try:
            resp = await self._client.get(self.base_url, params=params)
            resp.raise_for_status()
            data = resp.json()
            products = data.get("products", [])
            for product in products:
                nutriments = product.get("nutriments", {})
                calories = nutriments.get("energy-kcal_100g")
                if calories is not None:
                    return {
                        "calories_per_100g": calories,
                        "product_name": product.get("product_name"),
                        "brands": product.get("brands"),
                        "url": product.get("url"),
                    }
        except Exception:
            pass
        return None
