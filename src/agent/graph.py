from langgraph.graph import StateGraph, END
from .states import AgentState
from .clarification_agent import build_clarification_graph
from .recipe_retrieval_agent import build_recipe_retrieval_graph


def build_graph(checkpointer=None):
    graph = StateGraph(AgentState)
    
    clarification_subgraph = build_clarification_graph(checkpointer=checkpointer)
    graph.add_node("clarification", clarification_subgraph)
    
    recipe_retrieval_subgraph = build_recipe_retrieval_graph(checkpointer=checkpointer)
    graph.add_node("recipe_retrieval", recipe_retrieval_subgraph)
    
    graph.set_entry_point("clarification")
    graph.add_edge("clarification", "recipe_retrieval")
    graph.add_edge("recipe_retrieval", END)
    
    return graph.compile(checkpointer=checkpointer)