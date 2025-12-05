from langgraph.graph import StateGraph, END
from .states import AgentState
from .clarification_agent import build_clarification_graph


def build_graph():
    graph = StateGraph(AgentState)
    
    clarification_subgraph = build_clarification_graph()
    graph.add_node("clarification", clarification_subgraph)
    
    graph.set_entry_point("clarification")
    graph.add_edge("clarification", END)
    
    return graph.compile()