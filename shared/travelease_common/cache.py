from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: int = 120):
        self.ttl = timedelta(seconds=ttl_seconds)
        self._store: dict[str, tuple[datetime, Any]] = {}

    def get(self, key: str) -> Any | None:
        payload = self._store.get(key)
        if payload is None:
            return None
        expires_at, value = payload
        if datetime.now(UTC) > expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (datetime.now(UTC) + self.ttl, value)
