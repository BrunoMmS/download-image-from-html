import asyncio
import concurrent.futures

from fastapi import HTTPException
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.core.config import (
    MAX_CONCURRENT_RENDERS,
    REQUEST_TIMEOUT,
    SELECTOR_VIEWPORT_SIZE,
)

from app.utils.playwright_runner import (
    block_requests,
    create_browser,
    run_async_in_thread,
)


class ScreenshotService:

    def __init__(self):
        self._semaphore = asyncio.Semaphore(
            MAX_CONCURRENT_RENDERS
        )

        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=MAX_CONCURRENT_RENDERS
        )

    async def screenshot_page(
        self,
        html: str,
        width: int,
        height: int,
    ) -> bytes:

        async with self._semaphore:

            loop = asyncio.get_running_loop()

            return await loop.run_in_executor(
                self._executor,
                lambda: run_async_in_thread(
                    self._capture_page,
                    html,
                    width,
                    height,
                ),
            )

    async def screenshot_selector(
        self,
        html: str,
        selector: str,
    ) -> bytes | None:

        async with self._semaphore:

            loop = asyncio.get_running_loop()

            return await loop.run_in_executor(
                self._executor,
                lambda: run_async_in_thread(
                    self._capture_selector,
                    html,
                    selector,
                ),
            )

    async def _capture_page(
        self,
        html: str,
        width: int,
        height: int,
    ) -> bytes:

        p, browser = await create_browser()

        try:

            context = await browser.new_context(
                viewport={
                    "width": width,
                    "height": height,
                },
                java_script_enabled=False,
            )

            page = await context.new_page()

            await page.route(
                "**/*",
                block_requests,
            )

            try:

                await page.set_content(
                    html,
                    wait_until="domcontentloaded",
                    timeout=REQUEST_TIMEOUT,
                )

            except PlaywrightTimeoutError:

                raise HTTPException(
                    status_code=408,
                    detail="Timeout renderizando HTML",
                )

            screenshot = await page.screenshot(
                full_page=False,
                type="png",
                timeout=REQUEST_TIMEOUT,
            )

            await context.close()

            return screenshot

        finally:

            await browser.close()
            await p.stop()

    async def _capture_selector(
        self,
        html: str,
        selector: str,
    ) -> bytes | None:

        p, browser = await create_browser()

        try:

            context = await browser.new_context(
                viewport={
                    "width": SELECTOR_VIEWPORT_SIZE,
                    "height": SELECTOR_VIEWPORT_SIZE,
                },
                java_script_enabled=False,
            )

            page = await context.new_page()

            await page.route(
                "**/*",
                block_requests,
            )

            try:

                await page.set_content(
                    html,
                    wait_until="domcontentloaded",
                    timeout=REQUEST_TIMEOUT,
                )

            except PlaywrightTimeoutError:

                raise HTTPException(
                    status_code=408,
                    detail="Timeout renderizando HTML",
                )

            element = await page.query_selector(selector)

            if not element:
                await context.close()
                return None

            screenshot = await element.screenshot(
                type="png",
                scale="device",
                timeout=REQUEST_TIMEOUT,
            )

            await context.close()

            return screenshot

        finally:

            await browser.close()
            await p.stop()