import time
from typing import Any

_cache: dict[str, tuple[float, Any]] = {}
TTL = 60


def get(key: str):
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < TTL:
            return val
    return None


def set(key: str, value: Any):
    _cache[key] = (time.time(), value)
