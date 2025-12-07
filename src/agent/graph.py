from functools import partial
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from .states import AgentState
from .clarification_agent import build_clarification_graph
from .recipe_retrieval_agent import build_recipe_retrieval_graph
from .report_generation import build_report_generation_graph


# adapter to prevent leakage to the subgraph state and vice versa
async def call_subgraph(state: AgentState, subgraph: CompiledStateGraph) -> dict:
    input_state = {
        "user_recipe_query": state.user_recipe_query,
    }
    result = await subgraph.ainvoke(input_state)
    return {"selected_recipes": result.get("selected_recipes", [])}

def build_graph(checkpointer=None):
    graph = StateGraph(AgentState)
    
    clarification_subgraph = build_clarification_graph(checkpointer=checkpointer)
    graph.add_node("clarification", clarification_subgraph)
    
    recipe_retrieval_subgraph = build_recipe_retrieval_graph(checkpointer=checkpointer)
    call_retrieval = partial(call_subgraph, subgraph=recipe_retrieval_subgraph)
    graph.add_node("recipe_retrieval", call_retrieval)
    
    report_generation_subgraph = build_report_generation_graph(checkpointer=checkpointer)
    graph.add_node("report_generation", report_generation_subgraph)
    
    graph.set_entry_point("clarification")
    graph.add_edge("clarification", "recipe_retrieval")
    graph.add_edge("recipe_retrieval", "report_generation")
    graph.add_edge("report_generation", END)
    
    return graph.compile(checkpointer=checkpointer)