import time
import threading


class ScreenshotCache:

    def __init__(self, max_size: int = 32, ttl_seconds: int = 300):
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._store: dict[tuple[str, str], tuple[bytes, float]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, html: str, selector: str) -> bytes | None:
        key = (html, selector)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            data, ts = entry
            if time.monotonic() - ts > self._ttl:
                del self._store[key]
                self._misses += 1
                return None
            # Move to end (most recently used)
            del self._store[key]
            self._store[key] = (data, ts)
            self._hits += 1
            return data

    def set(self, html: str, selector: str, data: bytes) -> None:
        key = (html, selector)
        now = time.monotonic()
        with self._lock:
            if key in self._store:
                del self._store[key]
            while len(self._store) >= self._max_size:
                oldest = next(iter(self._store))
                del self._store[oldest]
            self._cleanup(now)
            self._store[key] = (data, now)

    def _cleanup(self, now: float) -> None:
        expired = [
            k for k, (_, ts) in self._store.items()
            if now - ts > self._ttl
        ]
        for k in expired:
            del self._store[k]
        while len(self._store) > self._max_size:
            oldest = next(iter(self._store))
            del self._store[oldest]

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    @property
    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._store),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{self._hits / total * 100:.1f}%" if total else "0%",
            }
