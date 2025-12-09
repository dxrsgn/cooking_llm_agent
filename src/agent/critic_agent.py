from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import END
from .states import RecipeSearchSubgraphState
from .utils import create_llm, StructuredRetryRunnable, batch_execute
from .schemas.structured_output import RecipeSelection
from .prompts import format_recipe_query, get_critic_prompt, format_critic_user_message, get_critic_negative_reason_summary


async def critic_agent_node(state: RecipeSearchSubgraphState, config: Optional[RunnableConfig] = None) -> dict:
    configurable = config.get("configurable", {}) if config else {}
    llm = create_llm(
        reasoning=configurable.get("reasoning", True),
        model=configurable.get("model_name"),
        temperature=0,
        api_key=configurable.get("llm_api_key"),
        base_url=configurable.get("llm_api_url"),
        max_tokens=4096,
    ).with_structured_output(RecipeSelection)
    
    retry_runnable = StructuredRetryRunnable(llm, RecipeSelection)

    batch_size = configurable.get("batch_size", 5)
    max_concurrent = configurable.get("max_parallel_tasks", 2)
    batches = [
        state.current_recipes[i:i + batch_size] for i
        in range(0, len(state.current_recipes), batch_size)
    ]

    async def process_batch(batch) -> RecipeSelection:
        recipes_text = "\n".join([
            f"Recipe ID: {recipe.id}\nTitle: {recipe.title}\nIngredients: {', '.join([ing.name for ing in recipe.ingredients])}\n"
            for recipe in batch
        ])
        query = state.user_recipe_query
        assert query is not None
        query_text = format_recipe_query(query)
        system_prompt = get_critic_prompt()
        user_message = format_critic_user_message(query_text, recipes_text)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        return await retry_runnable.ainvoke(messages)
    tasks = [process_batch(batch) for batch in batches]
    batched_result: list[RecipeSelection] = await batch_execute(tasks, max_concurrent)
    flattened_ids = [recipe_id for result in batched_result for recipe_id in result.selected_recipe_ids]
    set_selected_ids = set(flattened_ids)
    selected_recipes = [
        recipe for recipe in state.current_recipes
        if recipe.id in set_selected_ids
    ]


    llm = create_llm(
        reasoning=configurable.get("reasoning", True),
        model=configurable.get("model_name"),
        temperature=0,
        api_key=configurable.get("llm_api_key"),
        base_url=configurable.get("llm_api_url"),
        max_tokens=4096,
    )
    flattened_reasons = [result.reason for result in batched_result]
    reason_summary = await llm.ainvoke(
        [SystemMessage(content=get_critic_negative_reason_summary(flattened_reasons))]
    )
    
    return {
        "selected_recipes": selected_recipes,
        "messages": HumanMessage(content=reason_summary.content),
    }


def route_after_critic(state: RecipeSearchSubgraphState):
    # if no recipes found, go back to recipe search
    if not state.selected_recipes:
        return "recipe_search_agent"
    # take at least 2 iterations to get the best recipes
    if state.iterations < 2:
        return "recipe_search_agent"
    return END