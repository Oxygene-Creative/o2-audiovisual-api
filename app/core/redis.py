from faststream.redis import RedisBroker, fastapi
import os
import asyncio
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from fastapi import Depends

# Create shared broker instance
REDIS_URI = os.getenv("REDIS_URI", "redis://redis:6379")
redis_router = fastapi.RedisRouter(REDIS_URI)
redis_broker = RedisBroker(REDIS_URI)
redis_host = REDIS_URI.split("://")[-1]
redis_domain, redis_port = redis_host.split(":")
redis_client = Redis(host=redis_domain, port=redis_port, db=0, decode_responses=True)

audio_queue_busy_lock = asyncio.Lock()
video_queue_busy_lock = asyncio.Lock()
queue_busy_lock = asyncio.Lock()

def load_redis_client():
    global redis_client
    redis_host = REDIS_URI.split("://")[-1]
    redis_client = Redis(host=redis_host, port=6379, db=0, decode_responses=True)

async def close_redis_client():
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None

async def get_redis() -> Redis:
    return Redis.from_url(REDIS_URI)

async def get_pipe(redis: Redis = Depends(get_redis)) -> Pipeline:
    return redis.pipeline()

    
