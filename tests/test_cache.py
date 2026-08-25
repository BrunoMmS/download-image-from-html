import time
import threading
from app.core.cache import ScreenshotCache


def test_miss_on_empty_cache():
    cache = ScreenshotCache(max_size=10, ttl_seconds=60)
    result = cache.get("<html>test</html>", ".tarjeta")
    assert result is None
    assert cache.stats["misses"] == 1
    assert cache.stats["hits"] == 0


def test_hit_after_set():
    cache = ScreenshotCache(max_size=10, ttl_seconds=60)
    html = "<html>card</html>"
    data = b"\x89PNG\r\n\x1a\n"
    cache.set(html, ".tarjeta", data)
    result = cache.get(html, ".tarjeta")
    assert result == data
    assert cache.stats["hits"] == 1
    assert cache.stats["misses"] == 0


def test_miss_on_different_selector():
    cache = ScreenshotCache(max_size=10, ttl_seconds=60)
    html = "<html>card</html>"
    data = b"\x89PNG"
    cache.set(html, ".tarjeta", data)
    result = cache.get(html, "#card")
    assert result is None


def test_miss_on_different_html():
    cache = ScreenshotCache(max_size=10, ttl_seconds=60)
    data = b"\x89PNG"
    cache.set("<html>v1</html>", ".tarjeta", data)
    result = cache.get("<html>v2</html>", ".tarjeta")
    assert result is None


def test_ttl_expiration():
    cache = ScreenshotCache(max_size=10, ttl_seconds=0.01)
    html = "<html>expire</html>"
    cache.set(html, ".tarjeta", b"data")
    time.sleep(0.05)
    result = cache.get(html, ".tarjeta")
    assert result is None
    assert cache.stats["misses"] == 1


def test_lru_eviction():
    cache = ScreenshotCache(max_size=2, ttl_seconds=60)
    cache.set("h1", ".tarjeta", b"d1")
    cache.set("h2", ".tarjeta", b"d2")
    cache.set("h3", ".tarjeta", b"d3")
    assert cache.get("h1", ".tarjeta") is None
    assert cache.get("h2", ".tarjeta") == b"d2"
    assert cache.get("h3", ".tarjeta") == b"d3"


def test_lru_refreshes_on_access():
    cache = ScreenshotCache(max_size=2, ttl_seconds=60)
    cache.set("h1", ".tarjeta", b"d1")
    cache.set("h2", ".tarjeta", b"d2")
    cache.get("h1", ".tarjeta")
    cache.set("h3", ".tarjeta", b"d3")
    assert cache.get("h1", ".tarjeta") == b"d1"
    assert cache.get("h2", ".tarjeta") is None


def test_clear():
    cache = ScreenshotCache(max_size=10, ttl_seconds=60)
    cache.set("h1", ".tarjeta", b"d1")
    cache.set("h2", ".tarjeta", b"d2")
    cache.clear()
    assert cache.get("h1", ".tarjeta") is None
    assert cache.stats["hits"] == 0
    assert cache.stats["misses"] == 1


def test_overwrite_existing_key():
    cache = ScreenshotCache(max_size=10, ttl_seconds=60)
    html = "<html>overwrite</html>"
    cache.set(html, ".tarjeta", b"old")
    cache.set(html, ".tarjeta", b"new")
    result = cache.get(html, ".tarjeta")
    assert result == b"new"
    assert cache.stats["size"] == 1


def test_stats():
    cache = ScreenshotCache(max_size=5, ttl_seconds=60)
    cache.set("h1", ".tarjeta", b"d1")
    cache.get("h1", ".tarjeta")
    cache.get("h1", ".tarjeta")
    cache.get("h2", ".tarjeta")
    stats = cache.stats
    assert stats["size"] == 1
    assert stats["max_size"] == 5
    assert stats["hits"] == 2
    assert stats["misses"] == 1
    assert stats["hit_rate"] == "66.7%"


def test_concurrent_access():
    cache = ScreenshotCache(max_size=100, ttl_seconds=60)
    errors = []

    def writer(start):
        try:
            for i in range(start, start + 50):
                cache.set(f"h{i}", ".tarjeta", f"d{i}".encode())
        except Exception as e:
            errors.append(e)

    def reader(start):
        try:
            for i in range(start, start + 50):
                cache.get(f"h{i}", ".tarjeta")
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=writer, args=(0,)),
        threading.Thread(target=writer, args=(50,)),
        threading.Thread(target=reader, args=(0,)),
        threading.Thread(target=reader, args=(50,)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert cache.stats["size"] <= 100
