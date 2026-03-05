from faststream.redis import RedisBroker, fastapi
import os
import asyncio
from urllib.parse import urlparse
from redis import Redis as SyncRedis
from redis.cluster import key_slot
from redis.asyncio import Redis, RedisCluster
from redis.asyncio.cluster import ClusterNode
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


def _decode_host(host: str | bytes) -> str:
    if isinstance(host, bytes):
        return host.decode()
    return host


def _discover_broker_uri(redis_uri: str) -> str:
    seeds = _parse_seeds(redis_uri)
    if len(seeds) <= 1:
        return _first_seed_url(redis_uri)

    target_slot = key_slot(b"audiovisual:{av}:asr_stream")

    for seed in seeds:
        conn = None
        try:
            conn = SyncRedis(
                host=seed["host"],
                port=seed["port"],
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            slots = conn.execute_command("CLUSTER", "SLOTS")

            for slot in slots:
                start_slot = slot[0]
                end_slot = slot[1]
                master = slot[2]

                if start_slot <= target_slot <= end_slot:
                    host = _decode_host(master[0])
                    port = master[1]
                    return f"redis://{host}:{port}"
        except Exception:
            continue
        finally:
            if conn is not None:
                conn.close()

    return _first_seed_url(redis_uri)


REDIS_SEEDS = _parse_seeds(REDIS_URI)
BROKER_URI = os.getenv("REDIS_BROKER_URI", _discover_broker_uri(REDIS_URI))

redis_router = fastapi.RedisRouter(BROKER_URI)
redis_broker = RedisBroker(BROKER_URI)


def _cluster_startup_nodes() -> list[ClusterNode]:
    return [ClusterNode(seed["host"], seed["port"]) for seed in REDIS_SEEDS]


def _build_client() -> Redis | RedisCluster:
    if len(REDIS_SEEDS) > 1:
        return RedisCluster(
            startup_nodes=_cluster_startup_nodes(),
            decode_responses=True,
        )
    return Redis(
        host=REDIS_SEEDS[0]["host"],
        port=REDIS_SEEDS[0]["port"],
        db=0,
        decode_responses=True,
    )


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
        return RedisCluster(
            startup_nodes=_cluster_startup_nodes(),
            decode_responses=True,
        )
    return Redis.from_url(BROKER_URI)


async def get_pipe(redis: Redis = Depends(get_redis)) -> Pipeline:
    return redis.pipeline()
