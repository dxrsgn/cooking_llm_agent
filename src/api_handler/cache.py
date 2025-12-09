import json
import hashlib
from functools import wraps
from typing import Callable, Any
from redis.asyncio import Redis


def make_cache_key(prefix: str, *args, **kwargs) -> str:
    raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    h = hashlib.md5(raw.encode()).hexdigest()
    return f"{prefix}:{h}"


def redis_cache(prefix: str, ttl: int = 3600):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            redis: Redis | None = getattr(self, "_redis", None)
            cache_key = make_cache_key(prefix, *args, **kwargs)

            if redis:
                cached = await redis.get(cache_key)
                if cached:
                    return json.loads(cached)

            result = await func(self, *args, **kwargs)

            if redis and result is not None:
                await redis.set(cache_key, json.dumps(result, default=str), ex=ttl)

            return result
        return wrapper
    return decorator

