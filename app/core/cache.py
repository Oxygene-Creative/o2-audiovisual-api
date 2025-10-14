# cache_decorator.py
from functools import wraps
from typing import Callable, Any, Optional
import hashlib
import inspect
from app.core.redis import redis_client
import json

def cache_response(expire: Optional[int] = None, key_prefix: str = ""):

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Generate cache key based on function name and parameters
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Create a hash of the arguments
            args_str = str(sorted(bound_args.arguments.items()))
            args_hash = hashlib.md5(args_str.encode()).hexdigest()
            
            cache_key = f"{key_prefix}{func.__name__}:{args_hash}"
            
            # Try to get from cache first
            cached_result = redis_client.get(cache_key)
            if cached_result is not None:
                return json.loads(cached_result)
            
            # Execute function if not in cache
            result = await func(*args, **kwargs)
            
            # Store in Redis for 5 minutes
            redis_client.setex(cache_key, expire, json.dumps(result))
            return result
        return wrapper
        
    return decorator