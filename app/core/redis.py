from faststream.redis import RedisBroker
import os

# Create shared broker instance
redis_broker = RedisBroker(
    os.getenv("REDIS_URI", "redis://redis:6379")
)