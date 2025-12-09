from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage, get_buffer_string, AIMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from .states import AgentState
from .schemas.structured_output import ClarificationDecision, UserRecipeQuery
from .schemas.objects import UserProfile
from .prompts import get_clarification_prompt, get_schema_generation_prompt
from .utils import create_llm, StructuredRetryRunnable


async def clarification_node(state: AgentState, config: Optional[RunnableConfig] = None) -> Command:
    configurable = config.get("configurable", {}) if config else {}
    reasoning = configurable.get("reasoning", False)
    llm = create_llm(
        reasoning=reasoning,
        model=configurable.get("model_name"),
        temperature=0,
        api_key=configurable.get("llm_api_key"),
        base_url=configurable.get("llm_api_url"),
        max_tokens=4096,
    ).with_structured_output(ClarificationDecision)
    
    retry_runnable = StructuredRetryRunnable(llm, ClarificationDecision)
    
    conversation_history = get_buffer_string(state.messages)
    
    user_info = []
    if state.user_profile.preferences:
        user_info.append(f"<User preferences>{', '.join(state.user_profile.preferences)}</User preferences>")
    if state.user_profile.allergies:
        allergies_str = ', '.join(state.user_profile.allergies)
        user_info.append(f"<User allergies and restrictions>{allergies_str}</User allergies and restrictions>")
    if state.user_profile.last_queries:
        last_queries_str = ', '.join(state.user_profile.last_queries)
        user_info.append(f"<User previous queries>{last_queries_str}</User previous queries>")
    
    user_context = "\n".join(user_info) if user_info else ""
    
    system_prompt = get_clarification_prompt(
        user_context=user_context,
        conversation_history=conversation_history,
        reasoning=reasoning
    )
    
    messages = [
        SystemMessage(content=system_prompt)
    ]
    
    decision = await retry_runnable.ainvoke(messages)
    
    if decision.ask_more_questions == "yes":
        return Command(
            goto="asking_question",
            update={"messages": [AIMessage(content=decision.question)]},
        )
    
    return Command(
        goto="generate_schema",
        update={"messages": [AIMessage(content="No more questions needed")]},
    )

async def asking_question_node(state: AgentState, config: Optional[RunnableConfig] = None) -> dict:
    question = interrupt(state.messages[-1].content)
    
    return {"messages": [HumanMessage(content=question)]}

async def schema_generation_node(state: AgentState, config: Optional[RunnableConfig] = None) -> dict:
    configurable = config.get("configurable", {}) if config else {}
    reasoning = configurable.get("reasoning", False)
    llm = create_llm(
        reasoning=reasoning,
        model=configurable.get("model_name"),
        temperature=0,
        api_key=configurable.get("llm_api_key"),
        base_url=configurable.get("llm_api_url"),
        max_tokens=4096,
    ).with_structured_output(UserRecipeQuery)
    
    retry_runnable = StructuredRetryRunnable(llm, UserRecipeQuery)
    
    conversation_history = get_buffer_string(state.messages)
    
    user_info = []
    if state.user_profile.preferences:
        preferences_str = ', '.join(state.user_profile.preferences)
        user_info.append(f"<User preferences>{preferences_str}</User preferences>")
    if state.user_profile.allergies:
        allergies_str = ', '.join(state.user_profile.allergies)
        user_info.append(f"<User allergies and restrictions>{allergies_str}</User allergies and restrictions>")
    
    user_context = "\n".join(user_info) if user_info else ""
    
    system_prompt = get_schema_generation_prompt(
        user_context=user_context,
        conversation_history=conversation_history,
        reasoning=reasoning
    )
    
    messages = [SystemMessage(content=system_prompt)]
    
    final_query = await retry_runnable.ainvoke(messages)
    new_profile = UserProfile(
        last_queries=state.user_profile.last_queries + [final_query.query],
        preferences=state.user_profile.preferences,
        allergies=state.user_profile.allergies
    )

    return {"user_recipe_query": final_query, "user_profile": new_profile}


def build_clarification_graph(checkpointer=None):
    graph = StateGraph(AgentState)
    graph.add_node("clarify", clarification_node)
    graph.add_node("asking_question", asking_question_node)
    graph.add_node("generate_schema", schema_generation_node)
    graph.add_edge(START, "clarify")
    graph.add_edge("asking_question", "clarify")
    graph.add_edge("generate_schema", END)
    return graph.compile(checkpointer=checkpointer)