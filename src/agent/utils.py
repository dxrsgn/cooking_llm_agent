import asyncio
import json
from typing import TypeVar, Type, Any, Generic
from pydantic import BaseModel, ValidationError
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import PydanticOutputParser

T = TypeVar('T', bound=BaseModel)

def create_llm(reasoning=False, **kwargs):
    if reasoning:
        conf = {"reasoning": {"enabled": True, "effort": "high"}}
    else:
        conf = {"reasoning": {"enabled": False, "effort": "low"}}
    return ChatOpenAI(**kwargs | conf)

def clean_response(text: str) -> str:
    text = text.strip()
    text = text.replace('```json', '').replace('```', '')
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        return text[first_brace:last_brace+1]
    return text

def parse_with_retry(model_class: Type[T], raw_text: str) -> T:
    cleaned = clean_response(raw_text)
    try:
        data = json.loads(cleaned)
        return model_class(**data)
    except (json.JSONDecodeError, ValidationError):
        pass
    
    try:
        data = json.loads(raw_text)
        return model_class(**data)
    except (json.JSONDecodeError, ValidationError):
        pass
    
    raise ValueError(f"Failed to parse response after cleaning: {raw_text}")


# generic[T] and T as output typings is not neccesary, but it
# gives nice support for intellisense and type checking
class StructuredRetryRunnable(Runnable, Generic[T]):
    def __init__(
        self,
        llm: Runnable,
        model_class: Type[T],
        max_retries: int = 3
    ):
        super().__init__()
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=model_class)
        self.model_class = model_class
        self.max_retries = max_retries
    
    def invoke(self, input: Any, config: Any = None, **kwargs) -> T:
        # we dont really need sync, async would be enough
        raise NotImplementedError("This method is not implemented")
    
    async def ainvoke(self, input: Any, config: Any = None, **kwargs) -> T:
        messages = input if isinstance(input, list) else [input]
        
        for _ in range(self.max_retries):
            try:
                response = await self.llm.ainvoke(messages, config=config)
                if isinstance(response, BaseModel):
                    return response  # type: ignore
                if hasattr(response, 'content'):
                    if isinstance(response.content, list):
                        text_parts = []
                        for m in response.content:
                            if isinstance(m, str):
                                text_parts.append(m)
                            elif isinstance(m, dict):
                                if m.get("type") == "text":
                                    text = m.get("text") or m.get("content", [{"text": ""}])[0].get("text", "")
                                    text_parts.append(text)
                            else:
                                text_parts.append(str(m))
                        raw_text = "".join(text_parts)
                    else:
                        raw_text = str(response.content)
                else:
                    raw_text = str(response)
                
                try:
                    parsed = self.parser.parse(raw_text)
                    return parsed
                except (ValidationError, json.JSONDecodeError, ValueError):
                    cleaned_text = clean_response(raw_text)
                    parsed = parse_with_retry(self.model_class, cleaned_text)
                    return parsed
            except Exception as e:
                print(f"exception: {e}")
                pass
        
        raise ValueError(f"Failed after max retries: {messages}")


async def batch_execute(tasks, max_concurrent):
    results = []
    for i in range(0, len(tasks), max_concurrent):
        batch = tasks[i:i + max_concurrent]
        batch_results = await asyncio.gather(*batch)
        results.extend(batch_results)
        if i + max_concurrent < len(tasks):
            await asyncio.sleep(1)
    return results
