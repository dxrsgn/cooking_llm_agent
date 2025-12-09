from typing import Optional
from langchain_core.runnables.config import RunnableConfig
from .states import AgentState
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END


# for now we just manualy format the response, since i dont see there use case for llm
async def report_generation_node(state: AgentState, config: Optional[RunnableConfig] = None) -> dict:
    if len(state.selected_recipes) == 0:
        return {
            "messages": [
                AIMessage(content="No recipes found that match the user's query requirements. Please try again with different query.")
            ],
        }
    lines = ["Here are the recipes that match your query requirements:\n\n"]
    for recipe in state.selected_recipes:
        lines.append(f"## {recipe.title}  \n\n")
        lines.append("**Ingredients:**  \n")
        for ingredient in recipe.ingredients:
            if ingredient.amount:
                lines.append(f"- {ingredient.name} ({ingredient.amount})  \n")
            else:
                lines.append(f"- {ingredient.name}  \n")
        lines.append("\n")
        if recipe.total_calories:
            lines.append(f"**Total Calories:** {recipe.total_calories}  \n\n")
        else:
            lines.append("**Total Calories:** Not available  \n\n")
        if recipe.instructions:
            lines.append(f"**Description:**\n{recipe.instructions}  \n\n")
        else:
            lines.append("**Description:** Not available  \n\n")
    lines.append("If you don't like any of the recipes, please try again with different query.")
    
    return {
        "messages": [
            AIMessage(content="".join(lines))
        ],
    }

def build_report_generation_graph(checkpointer=None):
    graph = StateGraph(AgentState)
    graph.add_node("report_generation", report_generation_node)
    graph.set_entry_point("report_generation")
    graph.add_edge(START, "report_generation")
    graph.add_edge("report_generation", END)
    return graph.compile(checkpointer=checkpointer)
