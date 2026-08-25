from os import environ


MAX_HTML_SIZE = 4_000_000
MAX_WIDTH = 2000
MAX_HEIGHT = 2000
# Increase request timeout for heavy renders (ms)
REQUEST_TIMEOUT = 60000
ALLOWED_SELECTORS = {".tarjeta", "#card", ".ficha_dactilar", ".ficha-dactilar"}
"""ALLOWED_ORIGINS = [
    origin.strip()
    for origin in environ.get("ALLOW_ORIGINS", "").split(",")
    if origin.strip()
]
"""

# Reduce concurrency and rasterization for safer heavy tests
MAX_CONCURRENT_RENDERS = 1
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 800
SELECTOR_VIEWPORT_SIZE = 800
# Use device scale factor 1 to reduce raster work during testing
DEVICE_SCALE_FACTOR = 1

CACHE_MAX_SIZE = 32
CACHE_TTL_SECONDS = 300
