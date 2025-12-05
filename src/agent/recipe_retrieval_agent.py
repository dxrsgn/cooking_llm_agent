from typing import Optional
import json
from pydantic import ValidationError
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from .states import AgentState
from .utils import create_llm
from .prompts import get_recipe_search_prompt, format_recipe_query
from src.tools.recipes_tools import search_recipes_by_name, search_recipes_by_ingredient, RecipeSearchResult


async def recipe_search_agent_node(state: AgentState, config: Optional[RunnableConfig] = None) -> dict:
    if not state.user_recipe_query:
        return {"recipes": []}
    
    last_message = state.messages[-1] if state.messages else None

    if isinstance(last_message, ToolMessage):
        recipes = []
        for msg in state.messages:
            if not isinstance(msg, ToolMessage):
                continue
            if isinstance(msg.content, str):
                try:
                    content_dict = json.loads(msg.content)
                    tool_resp = RecipeSearchResult.model_validate(content_dict)
                except (json.JSONDecodeError, ValidationError) as e:
                    print(f"ValidationError: {e}")
                    continue
            elif isinstance(msg.content, dict):
                try:
                    tool_resp = RecipeSearchResult.model_validate(msg.content)
                except ValidationError as e:
                    print(f"ValidationError: {e}")
                    continue
            elif isinstance(msg.content, RecipeSearchResult):
                tool_resp = msg.content
            else:
                continue
            recipes.extend(tool_resp.recipes)
        
        seen_ids = set()
        unique_recipes = []
        for recipe in recipes:
            if recipe.id not in seen_ids:
                seen_ids.add(recipe.id)
                unique_recipes.append(recipe)
        
        return {"recipes": unique_recipes}
    
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
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query_text)
    ]
    
    response = await llm_with_tools.ainvoke(messages, config=config)
    
    return {"messages": [response]}


def build_recipe_retrieval_graph(checkpointer=None):
    tools = [search_recipes_by_name, search_recipes_by_ingredient]
    tool_node = ToolNode(tools)
    
    graph = StateGraph(AgentState)
    graph.add_node("recipe_search_agent", recipe_search_agent_node)
    graph.add_node("tools", tool_node)
    
    graph.add_edge(START, "recipe_search_agent")
    graph.add_conditional_edges(
        "recipe_search_agent",
        lambda state: "tools" if state.messages and hasattr(state.messages[-1], "tool_calls") and state.messages[-1].tool_calls else END
    )
    graph.add_edge("tools", "recipe_search_agent")
    
    return graph.compile(checkpointer=checkpointer)
