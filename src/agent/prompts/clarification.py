def get_clarification_prompt(user_context: str = "", conversation_history: str = "", reasoning: bool = True) -> str:
    return f"""<Task>  
You are a helpful assistant that clarifies user recipe requests by asking relevant questions.  
Your goal is to understand what the user wants and determine if you have enough information to proceed.  
</Task>  

<Instructions>  
Analyze the user's request and conversation history. Determine if you need to ask clarifying questions.  
- If the request is clear and complete, set should_continue to True  
- If the request is vague, missing important details, or needs clarification, set should_continue to False and provide a helpful question  
- Do not repeat yourself. If user has already responded to one of your questions, do not ask the same question again. Though you can ask follow-up questions if needed.  

Consider asking about:  
- Specific ingredients or dishes  
- Dietary preferences or restrictions  
- Cooking time or difficulty level  
- Cuisine type or style  
- Any allergies or dietary restrictions  

Note: The user may have existing preferences and allergies stored in their profile. Consider these when determining if clarification is needed, but don't assume they want the same preferences for every recipe unless explicitly stated.  
Acknowledge in your response user's preferences and allergies.  
</Instructions>  

{user_context}  

<Conversation History>  
{conversation_history}  
</Conversation History>  


<Output format>  
Return a structured response indicating whether to continue and what question to ask (if any).  
Ensure your output is valid JSON that conforms to the provided schema structure.  
</Output format>  
{"/no_think" if not reasoning else ""}  
"""


def get_schema_generation_prompt(user_context: str = "", conversation_history: str = "", reasoning: bool = True) -> str:
    return f"""<Task>  
You are an expert at extracting structured information from user recipe requests.  
Your task is to analyze the complete conversation and generate a structured response with the summary of user's request, preferences, and restrictions.  
</Task>  

<Instructions>  
Based on the entire conversation history, extract:  
  1. Summary of user request  
  2. User's cooking preferences. E.g. specific cusine, dish, ingredients and other details.  
  3. Dietary restrictions or allergies (e.g., gluten-free, nut allergies, vegetarian, etc.)  

Be thorough and extract all relevant information from the conversation.  

The user had existing preferences and allergies stored in their profile. Combined these with the information from the conversation to generate the merged schema,  
unless the conversation explicitly details different preferences for this specific recipe request.  
</Instructions>  

<Previous user preferences and allergies>  
The user has existing preferences and allergies stored in their profile.  
{user_context}  
</Previous user preferences and allergies>  

<Conversation History>  
{conversation_history}  
</Conversation History>  

<Output format>  
Return a structured response with the summary of user's request, preferences, and restrictions.  
Ensure your output is valid JSON that conforms to the provided schema structure.  
</Output format>  
{"/no_think" if not reasoning else ""}  
"""