"""In-memory per-client sliding-window rate limiter.

No external dependency. Suitable for the single-worker free HF Space deployment.
For multi-worker / multi-instance deployments, swap for Redis-backed limiting.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    """Sliding-window limiter: at most `max_requests` per `window_seconds` per key."""

    def __init__(self, *, max_requests: int = 5, window_seconds: float = 60.0) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, *, now: float | None = None) -> bool:
        """Record a hit for `key`. Return True if allowed, False if over the limit."""
        ts = time.monotonic() if now is None else now
        window = self._hits[key]
        cutoff = ts - self.window_seconds
        while window and window[0] <= cutoff:
            window.popleft()
        if len(window) >= self.max_requests:
            return False
        window.append(ts)
        return True


def client_key(*, x_forwarded_for: str | None, client_host: str | None) -> str:
    """Derive a rate-limit key. Prefer the first X-Forwarded-For hop (HF proxy), else client host."""
    if x_forwarded_for:
        first = x_forwarded_for.split(",")[0].strip()
        if first:
            return first
    return client_host or "unknown"
