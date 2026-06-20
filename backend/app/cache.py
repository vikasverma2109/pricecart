"""
Simple in-memory cache with TTL.
Replace with Redis for production multi-instance deployments.

Usage:
    cache = Cache(ttl_seconds=300)
    cache.set("key", value)
    value = cache.get("key")   # returns None if expired/missing
"""

import time
from typing import Any, Optional


class Cache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._store: dict[str, tuple[Any, float]] = {}

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (value, time.time())

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, ts = entry
        if time.time() - ts > self.ttl:
            del self._store[key]
            return None
        return value

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)


# Module-level singleton (5 min TTL by default)
cache = Cache(ttl_seconds=300)
