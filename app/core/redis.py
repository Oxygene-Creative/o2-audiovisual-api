from faststream.redis import RedisBroker, fastapi
import os
import redis.asyncio as redis

# Create shared broker instance
REDIS_URI = os.getenv("REDIS_URI", "redis://redis:6379")
redis_router = fastapi.RedisRouter(REDIS_URI)
redis_broker = RedisBroker(REDIS_URI)

# redis_client = None

# def load_redis_client():
#     global redis_client 
#     if redis_client is None:
#         redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
#     return redis_client

# async def close_redis_client():
#     if redis_client:
#         await redis_client.close()