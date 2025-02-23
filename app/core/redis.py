from faststream.redis import RedisBroker
import os

# Create shared broker instance
redis_broker = RedisBroker(
    os.getenv("REDIS_URI", "redis://redis:6379"),
    connection_kwargs={
        "retry_on_timeout": True,
        "socket_keepalive": True,
        "health_check_interval": 30
    }
)