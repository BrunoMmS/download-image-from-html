import asyncio
import sys

from playwright.async_api import async_playwright

from app.core.security import is_allowed_request

_PLAYWRIGHT = None
_BROWSER = None


def _ignore_connection_reset(loop, context):
    exc = context.get("exception")
    if isinstance(exc, ConnectionResetError):
        return
    loop.default_exception_handler(context)


# Helper to run an async coroutine in a fresh event loop (useful for Windows)
def run_async_in_thread(fn, *args, **kwargs):
    """
    Create a new event loop (Proactor on Windows) and run the coroutine `fn(*args, **kwargs)`
    to completion synchronously in the current thread. Intended to be called from a
    thread-pool worker (not from the main asyncio event loop).
    """
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_exception_handler(_ignore_connection_reset)

    try:
        return loop.run_until_complete(fn(*args, **kwargs))
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        try:
            loop.run_until_complete(loop.shutdown_default_executor())
        except Exception:
            pass
        loop.close()


async def start_browser():
    global _PLAYWRIGHT, _BROWSER

    if _BROWSER is not None:
        return _PLAYWRIGHT, _BROWSER

    if sys.platform == "win32":
        return None, None

    try:
        _PLAYWRIGHT = await async_playwright().start()
        _BROWSER = await _PLAYWRIGHT.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-setuid-sandbox",
            ],
        )
        return _PLAYWRIGHT, _BROWSER
    except Exception:
        _PLAYWRIGHT = None
        _BROWSER = None
        return None, None


async def stop_browser():
    global _PLAYWRIGHT, _BROWSER

    if _BROWSER is not None:
        await _BROWSER.close()
        _BROWSER = None

    if _PLAYWRIGHT is not None:
        await _PLAYWRIGHT.stop()
        _PLAYWRIGHT = None


async def block_requests(route):
    if is_allowed_request(route.request.url):
        await route.continue_()
    else:
        await route.abort()


async def create_browser():
    """
    Return a triple (p, browser, shared). If a global singleton browser was
    successfully started, return that and shared=True. Otherwise, create a
    fresh playwright instance and browser for this call and return shared=False.
    The caller should close browser/p if shared is False.
    """
    global _PLAYWRIGHT, _BROWSER

    if _BROWSER is not None:
        return _PLAYWRIGHT, _BROWSER, True

    # Create a new playwright + browser for this call. This function is async and
    # therefore must be run in an event loop — if the caller is running on a
    # loop that doesn't support subprocesses (Windows selector), the caller should
    # invoke this via run_async_in_thread inside a worker thread.
    p = await async_playwright().start()
    browser = await p.chromium.launch(
        headless=True,
        args=[
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-setuid-sandbox",
        ],
    )
    return p, browser, False