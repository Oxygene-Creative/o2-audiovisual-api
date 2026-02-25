from faststream.redis import RedisBroker, fastapi
import os
import asyncio
from urllib.parse import urlparse
from redis.asyncio import Redis, RedisCluster
from redis.asyncio.client import Pipeline
from fastapi import Depends

# Create shared broker instance
REDIS_URI = os.getenv("REDIS_URI", "redis://redis:6379")


def _normalize_seed(seed: str) -> str:
    seed = seed.strip()
    if "://" not in seed:
        seed = f"redis://{seed}"
    return seed


def _parse_seeds(redis_uri: str) -> list[dict]:
    seeds = []
    for part in redis_uri.split(","):
        if not part.strip():
            continue
        parsed = urlparse(_normalize_seed(part))
        host = parsed.hostname
        port = parsed.port or 6379
        if host:
            seeds.append({"host": host, "port": port})
    return seeds


def _first_seed_url(redis_uri: str) -> str:
    return _normalize_seed(redis_uri.split(",")[0])


REDIS_SEEDS = _parse_seeds(REDIS_URI)
BROKER_URI = _first_seed_url(REDIS_URI)

redis_router = fastapi.RedisRouter(BROKER_URI)
redis_broker = RedisBroker(BROKER_URI)


def _build_client() -> Redis | RedisCluster:
    if len(REDIS_SEEDS) > 1:
        return RedisCluster(startup_nodes=REDIS_SEEDS, decode_responses=True)
    return Redis(host=REDIS_SEEDS[0]["host"], port=REDIS_SEEDS[0]["port"], db=0, decode_responses=True)


redis_client = _build_client()

worker_1_busy_lock = asyncio.Lock()
worker_2_busy_lock = asyncio.Lock()
worker_3_busy_lock = asyncio.Lock()


def load_redis_client():
    global redis_client
    redis_client = _build_client()


async def close_redis_client():
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


async def get_redis() -> Redis:
    if len(REDIS_SEEDS) > 1:
        return RedisCluster(startup_nodes=REDIS_SEEDS, decode_responses=True)
    return Redis.from_url(BROKER_URI)


async def get_pipe(redis: Redis = Depends(get_redis)) -> Pipeline:
    return redis.pipeline()
