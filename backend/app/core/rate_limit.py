import asyncio
import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    """A simple sliding-window rate limiter, keyed by an arbitrary string.

    Deliberately in-memory: this stack has no Redis, and at this app's scale
    (a handful of admin/viewer accounts, a login form, not a public site)
    losing counters on process restart is an acceptable tradeoff. This also
    means correctness requires a single backend worker process (see
    deployment docs / gunicorn --workers 1) - documented as a known
    limitation in ARCHITECTURE.md.
    """

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        """Record a hit for `key` and return True if it is still within the limit."""
        now = time.monotonic()
        async with self._lock:
            bucket = self._hits[key]
            cutoff = now - window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= max_attempts:
                return False
            bucket.append(now)
            return True

    async def reset(self, key: str) -> None:
        async with self._lock:
            self._hits.pop(key, None)


login_rate_limiter = InMemoryRateLimiter()
