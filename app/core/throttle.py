from fastapi import FastAPI, Request, HTTPException
from functools import wraps
from typing import Callable
import time
from app.core.redis import redis_client

def get_client_ip(request: Request) -> str:
    """Extract client IP from X-Forwarded-For header or request client"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def rate_limit(max_requests: int, window_seconds: int):
    """
    Rate limiting decorator using Redis with sliding window counter
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs
            request = kwargs.get('request')
            if not request:
                # Try to find request in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                raise RuntimeError("Request object not found in route handler")
            
            # Get client IP
            client_ip = get_client_ip(request)
            
            # Create Redis key
            key = f"rate_limit:{func.__name__}:{client_ip}"
            
            # Current timestamp
            now = time.time()
            window_start = now - window_seconds
            
            # Use Redis pipeline for atomic operations
            pipe = redis_client.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiry on key
            pipe.expire(key, window_seconds)
            
            # Execute pipeline
            results = await pipe.execute()
            
            # Get count (result from zcard)
            request_count = results[1]
            
            # Check if rate limit exceeded
            if request_count >= max_requests:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds."
                )
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

