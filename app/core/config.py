from os import environ


MAX_HTML_SIZE = 200_000
MAX_WIDTH = 2000
MAX_HEIGHT = 2000
REQUEST_TIMEOUT = 5000
ALLOWED_SELECTORS = {".tarjeta", "#card"}
"""ALLOWED_ORIGINS = [
    origin.strip()
    for origin in environ.get("ALLOW_ORIGINS", "").split(",")
    if origin.strip()
]
"""

MAX_CONCURRENT_RENDERS = 2
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 800
SELECTOR_VIEWPORT_SIZE = 1200
