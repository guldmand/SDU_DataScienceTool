from __future__ import annotations
import contextlib, orjson
from typing import Any

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class RedisCache:
    def __init__(self, host="localhost", port=6379, ttl_s=60):
        if redis is None:
            raise RuntimeError("redis-py not installed")
        self.r = redis.Redis(host=host, port=port, decode_responses=False)
        self.ttl = ttl_s

    def get(self, key: bytes) -> Any | None:
        with contextlib.suppress(Exception):
            v = self.r.get(key)
            if v:
                return orjson.loads(v)
        return None

    def set(self, key: bytes, value: Any) -> None:
        self.r.setex(key, self.ttl, orjson.dumps(value))
