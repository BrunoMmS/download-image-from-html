import asyncio
import sys

from playwright.async_api import async_playwright

from app.core.security import is_allowed_request


def _ignore_connection_reset(loop, context):
    exc = context.get("exception")
    if isinstance(exc, ConnectionResetError):
        return
    loop.default_exception_handler(context)


def run_async_in_thread(fn, *args, **kwargs):
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


async def block_requests(route):
    if is_allowed_request(route.request.url):
        await route.continue_()
    else:
        await route.abort()


async def create_browser():
    p = await async_playwright().start()
    browser = await p.chromium.launch(
        headless=True,
        args=[
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-setuid-sandbox",
        ],
    )
    return p, browser
