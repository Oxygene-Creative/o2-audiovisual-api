import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


_log_lock = Lock()


def _default_replay_log_path() -> Path:
    cwd = Path(os.getcwd()).resolve()
    parent_logs = cwd.parent / "logs"
    if parent_logs.exists() or parent_logs.parent.exists():
        return parent_logs / "av_replay_candidates.jsonl"
    return cwd / "logs" / "av_replay_candidates.jsonl"


def get_replay_log_path() -> Path:
    configured = os.getenv("SEGMENTATION_REPLAY_LOG_PATH", "").strip()
    if configured:
        return Path(configured)
    return _default_replay_log_path()


def write_replay_candidate(event: dict) -> str:
    path = get_replay_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event,
    }

    with _log_lock:
        with path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload, ensure_ascii=True) + "\n")

    return str(path)
