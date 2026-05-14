# main.py
import asyncio
import sys
import concurrent.futures
from fastapi import FastAPI, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _run_playwright_sync(fn, *args, **kwargs):
    """Corre una función async de Playwright en un thread con su propio event loop."""
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()

    try:
        return loop.run_until_complete(fn(*args, **kwargs))
    finally:
        loop.close()


async def _screenshot_page(html: str, width: int, height: int) -> bytes:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": height})
        await page.set_content(html, wait_until="networkidle")
        screenshot = await page.screenshot(full_page=False, type="png")
        await browser.close()
    return screenshot


async def _screenshot_selector(html: str, selector: str, scale: str) -> bytes | None:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1200, "height": 1200})
        await page.set_content(html, wait_until="networkidle")
        element = await page.query_selector(selector)
        if not element:
            await browser.close()
            return None
        screenshot = await element.screenshot(type="png", scale="device")
        await browser.close()
    return screenshot


@app.post("/html-to-image")
async def html_to_image(
    html: str = Form(...),
    width: int = Form(default=800),
    height: int = Form(default=800),
):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_run_playwright_sync, _screenshot_page, html, width, height)
        screenshot = future.result()

    return Response(
        content=screenshot,
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=necrologica.png"},
    )


@app.post("/html-to-image/selector")
async def html_to_image_selector(
    html: str = Form(...),
    selector: str = Form(default=".tarjeta"),
    scale: str = Form(default="device"),  
):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_run_playwright_sync, _screenshot_selector, html, selector, scale)
        screenshot = future.result()

    if screenshot is None:
        return Response(content=b"Selector no encontrado", status_code=404)

    return Response(
        content=screenshot,
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=tarjeta.png"},
    )