from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langchain_core.runnables.config import RunnableConfig
from fastapi import HTTPException

from backend.config import LLM_MODEL_NAME, LLM_API_KEY, LLM_API_URL, LLM_REASONING
from backend.dependencies import app_state
from src.agent.schemas.objects import UserProfile
from src.agent.states import AgentState


def build_graph_config(thread_id: str) -> RunnableConfig:
    return {
        "configurable": {
            "thread_id": thread_id,
            "model_name": LLM_MODEL_NAME,
            "llm_api_key": LLM_API_KEY,
            "llm_api_url": LLM_API_URL,
            "reasoning": LLM_REASONING,
            "recipes_client": app_state.recipes_client,
            "nutrition_client": app_state.nutrition_client,
            "redis": app_state.redis,
        }
    }


def build_user_profile(db_profile) -> UserProfile:
    if not db_profile:
        return UserProfile()
    return UserProfile(
        last_queries=list(db_profile.last_queries or []),
        preferences=list(db_profile.preferences or []),
        allergies=list(db_profile.allergies or [])
    )


async def invoke_graph(message: str, user_profile: UserProfile, config: RunnableConfig) -> dict:
    if app_state.checkpointer is None or app_state.graph is None:
        raise HTTPException(status_code=503, detail="Service is not ready")
    
    state_snapshot = await app_state.graph.aget_state(config)
    tasks = state_snapshot.tasks if state_snapshot else None
    # for now only 1 parallel interrupt is supported
    (task, ) = tasks if tasks else (None, )
    (interrupt, ) = task.interrupts if task and task.interrupts else (None, )
    
    if interrupt and interrupt.value:
        return await app_state.graph.ainvoke(Command(resume=message), config=config)
    
    state = AgentState(
        messages=[HumanMessage(content=message)],
        user_profile=user_profile
    )
    return await app_state.graph.ainvoke(state, config=config)


def extract_response_message(result: dict) -> str:
    if "__interrupt__" in result and result["__interrupt__"]:
        return result["__interrupt__"][0].value
    
    if result.get("messages") and len(result["messages"]) > 0:
        last_message = result["messages"][-1]
        return last_message.content if hasattr(last_message, "content") else str(last_message)
    
    return "No message available"

