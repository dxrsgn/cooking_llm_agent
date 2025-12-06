from typing import Optional
import json
from langgraph.types import Command
from pydantic import ValidationError
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from .states import RecipeSearchSubgraphState
from .utils import create_llm, StructuredRetryRunnable, batch_execute
from .models import RecipeSelection
from .prompts import get_recipe_search_prompt, format_recipe_query, get_critic_prompt, format_critic_user_message, get_critic_negative_reason_summary
from src.tools.recipes_tools import search_recipes_by_name, search_recipes_by_ingredient, RecipeSearchResult


async def recipe_search_agent_node(state: RecipeSearchSubgraphState, config: Optional[RunnableConfig] = None) -> Command:
    last_message = state.messages[-1] if state.messages else None

    if isinstance(last_message, ToolMessage):
        return Command(goto="critic_agent")
    
    configurable = config.get("configurable", {}) if config else {}
    llm = create_llm(
        reasoning=configurable.get("reasoning", False),
        model=configurable.get("model_name"),
        temperature=0,
        api_key=configurable.get("llm_api_key"),
        base_url=configurable.get("llm_api_url"),
        max_tokens=4096,
    )
    
    tools = [search_recipes_by_name, search_recipes_by_ingredient]
    llm_with_tools = llm.bind_tools(tools)
    
    query = state.user_recipe_query
    query_text = format_recipe_query(query)
    
    system_prompt = get_recipe_search_prompt()
    
    messages = state.messages + [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query_text)
    ]
    
    response = await llm_with_tools.ainvoke(messages, config=config)
    
    return Command(
        goto="tools",
        update={
            "messages": [response],
            "iterations": state.iterations + 1,
        }
    )

# purely programmatic node to process tool messages and accumulate recipes
async def tool_post_process(state: RecipeSearchSubgraphState, config: Optional[RunnableConfig] = None) -> dict:
    recipes = []
    tool_messages = []
    for msg in state.messages:
        if not isinstance(msg, ToolMessage):
            continue
        if isinstance(msg.content, str):
            try:
                content_dict = json.loads(msg.content)
                tool_resp = RecipeSearchResult.model_validate(content_dict)
            except (json.JSONDecodeError, ValidationError) as e:
                continue
        elif isinstance(msg.content, dict):
            try:
                tool_resp = RecipeSearchResult.model_validate(msg.content)
            except ValidationError as e:
                continue
        elif isinstance(msg.content, RecipeSearchResult):
            tool_resp = msg.content
        else:
            continue
        tool_messages.append(msg)
        recipes.extend(tool_resp.recipes)
    
    seen_ids = set()
    unique_recipes = []
    for recipe in recipes:
        if recipe.id not in seen_ids:
            seen_ids.add(recipe.id)
            unique_recipes.append(recipe)

    # replacing content for context handling
    for msg in tool_messages:
        msg.content = "Successfully retrieved recipes"
    
    return {"current_recipes": unique_recipes, "messages": tool_messages}


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

def build_recipe_retrieval_graph(checkpointer=None):
    tools = [search_recipes_by_name, search_recipes_by_ingredient]
    tool_node = ToolNode(tools)
    
    graph = StateGraph(RecipeSearchSubgraphState)
    graph.add_node("recipe_search_agent", recipe_search_agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("tool_post_process", tool_post_process)
    graph.add_node("critic_agent", critic_agent_node)
    
    graph.add_edge(START, "recipe_search_agent")
    
    def route_after_critic(state: RecipeSearchSubgraphState):
        if state.iterations < 2:
            return "recipe_search_agent"
        else:
            return END
    
    graph.add_conditional_edges("critic_agent", route_after_critic)
    graph.add_edge("tools", "tool_post_process")
    graph.add_edge("tool_post_process", "recipe_search_agent")
    
    return graph.compile(checkpointer=checkpointer)
