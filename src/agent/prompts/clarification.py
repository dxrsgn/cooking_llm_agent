def get_clarification_prompt(user_context: str = "", conversation_history: str = "", reasoning: bool = True) -> str:
    return f"""<Task>
You are a helpful assistant that clarifies user recipe requests by asking relevant questions.
Your goal is to understand what the user wants and determine if you have enough information to proceed.
</Task>

<Instructions>
Analyze the user's request and conversation history. Determine if you need to ask clarifying questions.
- If the request is clear and complete, set should_continue to True
- If the request is vague, missing important details, or needs clarification, set should_continue to False and provide a helpful question

Consider asking about:
- Specific ingredients or dishes
- Dietary preferences or restrictions
- Cooking time or difficulty level
- Number of servings
- Cuisine type or style
- Any allergies or dietary restrictions

Note: The user may have existing preferences and allergies stored in their profile. Consider these when determining if clarification is needed, but don't assume they want the same preferences for every recipe unless explicitly stated.
</Instructions>

{user_context}

<Conversation History>
{conversation_history}
</Conversation History>

{"/no_think" if not reasoning else ""}

<Output format>
Return a structured response indicating whether to continue and what question to ask (if any).
Ensure your output is valid JSON that conforms to the provided schema structure.
</Output format>
"""


def get_schema_generation_prompt(user_context: str = "", conversation_history: str = "", reasoning: bool = True) -> str:
    return f"""<Task>
You are an expert at extracting structured information from user recipe requests.
Your task is to analyze the complete conversation and generate a structured query schema.
</Task>

<Instructions>
Based on the entire conversation history, extract:
- The main recipe query or request (summarized)
- User's dietary preferences (e.g., vegetarian, vegan, keto, etc.)
- Dietary restrictions or allergies (e.g., gluten-free, nut allergies, etc.)

Be thorough and extract all relevant information from the conversation.

Note: The user has existing preferences and allergies stored in their profile. Include these in your extraction unless the conversation explicitly indicates different preferences for this specific recipe request. Combine information from the conversation with the user's stored profile data.
</Instructions>

{user_context}

<Conversation History>
{conversation_history}
</Conversation History>

{"/no_think" if not reasoning else ""}

<Output format>
Return a structured query schema with the user's request, preferences, and restrictions.
Ensure your output is valid JSON that conforms to the provided schema structure.
</Output format>
"""