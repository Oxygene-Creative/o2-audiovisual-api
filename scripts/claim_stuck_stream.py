#!/usr/bin/env python3
import os
import sys
from urllib.parse import urlparse
from redis import Redis, RedisCluster
from redis.exceptions import ResponseError


def _env_int(name: str, default: int | None) -> int | None:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        print(f"Invalid integer for {name}: {value}", file=sys.stderr)
        sys.exit(2)


def main() -> int:
    redis_uri = os.getenv(
        "REDIS_URI",
        "redis://redis-node-1:7000,redis://redis-node-2:7001,redis://redis-node-3:7002",
    )
    stream = os.getenv("STREAM", "audiovisual:asr_stream")
    group = os.getenv("GROUP", "audiovisual:asr_group")
    consumer = os.getenv("CONSUMER", "asr_reclaimer")
    min_idle_ms = _env_int("MIN_IDLE_MS", None)
    if min_idle_ms is None:
        min_idle_minutes = _env_int("MIN_IDLE_MINUTES", 15)
        min_idle_ms = int(min_idle_minutes) * 60 * 1000
    count = _env_int("COUNT", 100)
    dry_run = os.getenv("DRY_RUN", "false").strip().lower() == "true"

    def _normalize_seed(seed: str) -> str:
        seed = seed.strip()
        if "://" not in seed:
            seed = f"redis://{seed}"
        return seed

    def _parse_seeds(value: str) -> list[dict]:
        seeds = []
        for part in value.split(","):
            if not part.strip():
                continue
            parsed = urlparse(_normalize_seed(part))
            host = parsed.hostname
            port = parsed.port or 6379
            if host:
                seeds.append({"host": host, "port": port})
        return seeds

    seeds = _parse_seeds(redis_uri)
    if len(seeds) > 1:
        client = RedisCluster(startup_nodes=seeds, decode_responses=True)
    else:
        client = Redis.from_url(_normalize_seed(
            redis_uri), decode_responses=True)

    stream_exists = True
    try:
        client.xinfo_stream(stream)
    except ResponseError:
        stream_exists = False

    if not stream_exists:
        try:
            client.xadd(stream, {"init": "1"})
        except ResponseError as exc:
            print(f"XADD failed: {exc}", file=sys.stderr)
            return 1

    try:
        client.xgroup_create(stream, group, id="$", mkstream=False)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            print(f"XGROUP CREATE failed: {exc}", file=sys.stderr)
            return 1

    try:
        pending_summary = client.xpending(stream, group)
    except ResponseError as exc:
        print(f"XPENDING failed: {exc}", file=sys.stderr)
        return 1

    total_pending = pending_summary["pending"] if isinstance(
        pending_summary, dict) else pending_summary[0]
    if total_pending == 0:
        print("No pending entries to claim.")
        return 0

    try:
        pending_entries = client.xpending_range(
            stream,
            group,
            min="-",
            max="+",
            count=count,
            consumername=None,
        )
    except ResponseError as exc:
        print(f"XPENDING RANGE failed: {exc}", file=sys.stderr)
        return 1

    stale_ids = []
    for pending in pending_entries:
        if isinstance(pending, dict):
            entry_id = pending.get("message_id")
            idle_ms = pending.get("time_since_delivered", 0)
        else:
            entry_id = pending[0]
            idle_ms = pending[2]

        if entry_id and idle_ms >= min_idle_ms:
            stale_ids.append(entry_id)

    if not stale_ids:
        print("No stale entries found.")
        return 0

    if dry_run:
        print(
            f"DRY_RUN=true. Would claim {len(stale_ids)} entries: {stale_ids[:10]}")
        return 0

    try:
        claimed = client.xclaim(
            stream,
            group,
            consumer,
            min_idle_ms,
            stale_ids,
            justid=True,
        )
    except ResponseError as exc:
        print(f"XCLAIM failed: {exc}", file=sys.stderr)
        return 1

    print(f"Claimed {len(claimed)} entries for consumer '{consumer}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
