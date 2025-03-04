from faststream.redis import fastapi
import os

REDIS_URI = os.getenv("REDIS_URI", "redis://redis:6379")
redis_router = fastapi.RedisRouter(REDIS_URI)