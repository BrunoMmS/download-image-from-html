import asyncio

from fastapi import HTTPException
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.core.config import (
    MAX_CONCURRENT_RENDERS,
    REQUEST_TIMEOUT,
    SELECTOR_VIEWPORT_SIZE,
)

from app.utils.playwright_runner import block_requests, create_browser


class ScreenshotService:

    def __init__(self):
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_RENDERS)

    async def screenshot_page(
        self,
        html: str,
        width: int,
        height: int,
    ) -> bytes:
        async with self._semaphore:
            return await self._capture_page(html, width, height)

    async def screenshot_selector(
        self,
        html: str,
        selector: str,
    ) -> bytes | None:
        async with self._semaphore:
            return await self._capture_selector(html, selector)

    async def _capture_page(
        self,
        html: str,
        width: int,
        height: int,
    ) -> bytes:
        _, browser = await create_browser()

        context = await browser.new_context(
            viewport={
                "width": width,
                "height": height,
            },
            java_script_enabled=False,
            device_scale_factor=2,
        )

        try:
            page = await context.new_page()

            await page.route("**/*", block_requests)

            try:
                await page.set_content(
                    html,
                    wait_until="domcontentloaded",
                    timeout=REQUEST_TIMEOUT,
                )
            except PlaywrightTimeoutError as exc:
                raise HTTPException(
                    status_code=408,
                    detail="Timeout renderizando HTML",
                ) from exc

            screenshot = await page.screenshot(
                full_page=False,
                type="png",
                timeout=REQUEST_TIMEOUT,
            )

            return screenshot
        finally:
            await context.close()

    async def _capture_selector(
        self,
        html: str,
        selector: str,
    ) -> bytes | None:
        _, browser = await create_browser()

        context = await browser.new_context(
            viewport={
                "width": SELECTOR_VIEWPORT_SIZE,
                "height": SELECTOR_VIEWPORT_SIZE,
            },
            java_script_enabled=False,
            device_scale_factor=2,
        )

        try:
            page = await context.new_page()

            await page.route("**/*", block_requests)

            try:
                await page.set_content(
                    html,
                    wait_until="domcontentloaded",
                    timeout=REQUEST_TIMEOUT,
                )
            except PlaywrightTimeoutError as exc:
                raise HTTPException(
                    status_code=408,
                    detail="Timeout renderizando HTML",
                ) from exc

            element = await page.query_selector(selector)
            if not element:
                return None

            return await element.screenshot(
                type="png",
                scale="device",
                timeout=REQUEST_TIMEOUT,
            )
        finally:
            await context.close()