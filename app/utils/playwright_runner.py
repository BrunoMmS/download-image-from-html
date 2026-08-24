import asyncio

from playwright.async_api import async_playwright

from app.core.security import is_allowed_request

_PLAYWRIGHT = None
_BROWSER = None


def _ignore_connection_reset(loop, context):
    exc = context.get("exception")
    if isinstance(exc, ConnectionResetError):
        return
    loop.default_exception_handler(context)


async def start_browser():
    global _PLAYWRIGHT, _BROWSER

    if _BROWSER is not None:
        return _PLAYWRIGHT, _BROWSER

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
    return await start_browser()
