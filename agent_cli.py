import asyncio
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from src.agent.graph import build_graph
from src.agent.models import UserProfile
from src.agent.states import AgentState
from src.api_handler.recipes_client import RecipesAPIClient

from phoenix.otel import register
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from openinference.instrumentation.langchain import LangChainInstrumentor


tracer_provider = register(
    project_name="aboba",
    auto_instrument=False,
)
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
HTTPXClientInstrumentor().instrument()
tracer = tracer_provider.get_tracer("aboba")

load_dotenv()


async def test_clarification():
    user_profile = UserProfile(
        preferences=["vegetarian", "low-carb"],
        allergies=["peanuts", "shellfish"]
    )
    
    state = AgentState(
        messages=[HumanMessage(content="I want to make something for dinner")],
        user_profile=user_profile
    )
    
    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)
    
    recipes_client = RecipesAPIClient()
    
    try:
        config = {
            "configurable": {
                "thread_id": "clarification-test-123",
                "model_name": os.getenv("LLM_MODEL_NAME", "gpt-4o-mini"),
                "llm_api_key": os.getenv("LLM_API_KEY"),
                "llm_api_url": os.getenv("LLM_API_URL"),
                "reasoning": os.getenv("LLM_REASONING", "false").lower() == "true",
                "recipes_client": recipes_client
            }
        }
        
        print("Starting clarification test...")
        print(f"User preferences: {user_profile.preferences}")
        print(f"User allergies: {user_profile.allergies}")
        print(f"Initial query: {state.messages[0].content}\n")
        
        result = await graph.ainvoke(state, config=config)
        
        while "__interrupt__" in result and result["__interrupt__"]:
            interrupt_info = result["__interrupt__"][0]
            print(f"\n=== Clarification Question ===")
            print(f"Question: {interrupt_info.value}")
            
            user_answer = input("\nYour answer: ")
            result = await graph.ainvoke(Command(resume=user_answer), config=config)
        
        if result.get("user_recipe_query"):
            print("\n=== Final Query Schema ===")
            print(f"Query: {result['user_recipe_query'].query}")
            print(f"Preferences: {result['user_recipe_query'].preferences}")
            print(f"Restrictions: {result['user_recipe_query'].restrictions}")
            
            if result.get("recipes"):
                print(f"\n=== Retrieved Recipes ({len(result['recipes'])}) ===")
                for i, recipe in enumerate(result['recipes'][:5], 1):
                    print(f"\n{i}. {recipe.title}")
                    print(f"   ID: {recipe.id}")
                    if recipe.ingredients:
                        ingredient_names = [ing.name for ing in recipe.ingredients[:3]]
                        print(f"   Ingredients: {', '.join(ingredient_names)}...")
            else:
                print("\nNo recipes retrieved")
        else:
            print("\nClarification completed but no final query generated")
    finally:
        await recipes_client.close()


def main():
    asyncio.run(test_clarification())


if __name__ == "__main__":
    main()
