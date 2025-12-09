from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig
from .states import RecipeSearchSubgraphState
from .utils import create_llm, batch_execute, StructuredRetryRunnable
from .prompts import get_calories_estimation_system_prompt, format_calories_estimation_prompt
from src.api_handler.nutrition_client import NutritionAPIClient
from src.api_handler.nutrition_funcs import enrich_recipes_with_nutrition
from src.api_handler.datamodels import CaloriesResponse


async def enrich_and_estimate_calories_node(state: RecipeSearchSubgraphState, config: Optional[RunnableConfig] = None) -> dict:
    recipes = getattr(state, "current_recipes", [])
    if not recipes:
        return {"messages": [HumanMessage(content="No recipes found to enrich")]}

    configurable = config.get("configurable", {}) if config else {}

    nutrition_client = NutritionAPIClient()
    enriched_recipes = await enrich_recipes_with_nutrition(recipes, nutrition_client)
    await nutrition_client.close()

    llm = create_llm(
        reasoning=configurable.get("reasoning", True),
        model=configurable.get("model_name"),
        temperature=0,
        api_key=configurable.get("llm_api_key"),
        base_url=configurable.get("llm_api_url"),
        max_tokens=4096,
    ).with_structured_output(CaloriesResponse)
    retry_runnable = StructuredRetryRunnable(llm, CaloriesResponse)

    batch_size = configurable.get("batch_size", 5)
    max_concurrent = configurable.get("max_parallel_tasks", 2)
    batches = [
        enriched_recipes[i:i + batch_size] for i
        in range(0, len(enriched_recipes), batch_size)
    ]

    async def process_batch(batch):
        recipes_data = []
        for recipe in batch:
            ingredients = []
            for ing in recipe.ingredients:
                ingredients.append({
                    "name": ing.name,
                    "amount": ing.amount or "unknown amount",
                    "calories": ing.calories_per100g if ing.calories_per100g is not None else "unknown calories"
                })
            recipes_data.append({"id": recipe.id, "title": recipe.title, "ingredients": ingredients})

        messages = [
            SystemMessage(content=get_calories_estimation_system_prompt()),
            HumanMessage(content=format_calories_estimation_prompt(recipes_data))
        ]
        return await retry_runnable.ainvoke(messages)

    tasks = [process_batch(batch) for batch in batches]
    batched_results: list[CaloriesResponse] = await batch_execute(tasks, max_concurrent)

    id_to_calories = {}
    for result in batched_results:
        for item in result.root:
            id_to_calories[item.id] = item.total_calories

    updated_recipes = []
    for recipe in enriched_recipes:
        total_cals = id_to_calories.get(recipe.id)
        updated_recipe = recipe.copy(update={"total_calories": total_cals})
        updated_recipes.append(updated_recipe)

    return {"current_recipes": updated_recipes}

