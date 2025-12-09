from typing import Optional
import json
import re
from langgraph.types import Command
from pydantic import ValidationError
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode
from .states import RecipeSearchSubgraphState
from .utils import create_llm
from .prompts import get_recipe_search_prompt, format_recipe_query
from .calorie_enrichment_agent import enrich_and_estimate_calories_node
from src.agent.critic_agent import critic_agent_node, route_after_critic
from src.tools.recipes_tools import search_recipes_by_name, search_recipes_by_ingredient, RecipeSearchResult


async def recipe_search_agent_node(state: RecipeSearchSubgraphState, config: Optional[RunnableConfig] = None) -> Command:
    last_message = state.messages[-1] if state.messages else None

    # got recipies, going to critizize them
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
    
    messages = state.messages
    if len(messages) == 0:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query_text)
        ]
    
    response = await llm_with_tools.ainvoke(messages, config=config)
    
    return Command(
        goto="tools",
        update={
            "messages": messages + [response],
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
        # sometimes model outputs bad formated ids
        match = re.search(r'(\d+)$', recipe.id)
        normalized_id = match.group(1) if match else recipe.id
        recipe.id = normalized_id
        if recipe.id not in seen_ids:
            seen_ids.add(recipe.id)
            unique_recipes.append(recipe)

    # replacing content for context handling
    for msg in tool_messages:
        msg.content = "Successfully retrieved recipes"
    
    return {"current_recipes": unique_recipes, "messages": tool_messages}


def build_recipe_retrieval_graph(checkpointer=None):
    tools = [search_recipes_by_name, search_recipes_by_ingredient]
    tool_node = ToolNode(tools)
    
    graph = StateGraph(RecipeSearchSubgraphState)
    
    graph.add_node("recipe_search_agent", recipe_search_agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("tool_post_process", tool_post_process)
    graph.add_node("enrich_calories", enrich_and_estimate_calories_node)
    graph.add_node("critic_agent", critic_agent_node)
    
    graph.add_edge(START, "recipe_search_agent")
    graph.add_edge("recipe_search_agent", "tools")
    graph.add_edge("tools", "tool_post_process")
    graph.add_edge("tool_post_process", "enrich_calories") 
    graph.add_edge("enrich_calories", "critic_agent")
    
    
    graph.add_conditional_edges("critic_agent", route_after_critic)
    
    return graph.compile(checkpointer=checkpointer)
