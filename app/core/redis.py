from faststream.redis import RedisBroker, fastapi
import os

# Create shared broker instance
REDIS_URI = os.getenv("REDIS_URI", "redis://redis:6379")
redis_router = fastapi.RedisRouter(REDIS_URI)
redis_broker = RedisBroker(REDIS_URI)