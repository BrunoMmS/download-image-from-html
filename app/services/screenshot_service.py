import asyncio
import sys
import concurrent.futures

import sys
import time
import concurrent.futures

from fastapi import HTTPException
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.core.config import (
    MAX_CONCURRENT_RENDERS,
    REQUEST_TIMEOUT,
    SELECTOR_VIEWPORT_SIZE,
    DEVICE_SCALE_FACTOR,
)

from app.utils.playwright_runner import block_requests, create_browser, run_async_in_thread


class ScreenshotService:

    def __init__(self):
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_RENDERS)
        # On Windows, use a ThreadPoolExecutor + run_async_in_thread fallback because
        # the running asyncio loop may not support subprocesses required by Playwright.
        self._executor = None
        if sys.platform == "win32":
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
            if self._executor is not None:
                loop = asyncio.get_running_loop()
                # run the async capture in a worker thread with its own event loop
                return await loop.run_in_executor(
                    self._executor,
                    lambda: run_async_in_thread(
                        self._capture_page,
                        html,
                        width,
                        height,
                    ),
                )
            return await self._capture_page(html, width, height)

    async def screenshot_selector(
        self,
        html: str,
        selector: str,
    ) -> bytes | None:
        async with self._semaphore:
            if self._executor is not None:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(
                    self._executor,
                    lambda: run_async_in_thread(
                        self._capture_selector,
                        html,
                        selector,
                    ),
                )
            return await self._capture_selector(html, selector)

    async def _capture_page(
        self,
        html: str,
        width: int,
        height: int,
    ) -> bytes:
        start_total = time.monotonic()
        p, browser, shared = await create_browser()

        t0 = time.monotonic()
        context = await browser.new_context(
            viewport={
                "width": width,
                "height": height,
            },
            java_script_enabled=False,
            device_scale_factor=DEVICE_SCALE_FACTOR,
        )
        t1 = time.monotonic()

        try:
            page = await context.new_page()

            await page.route("**/*", block_requests)

            try:
                t_before_set = time.monotonic()
                await page.set_content(
                    html,
                    wait_until="domcontentloaded",
                    timeout=REQUEST_TIMEOUT,
                )
                t_after_set = time.monotonic()
            except PlaywrightTimeoutError as exc:
                raise HTTPException(
                    status_code=408,
                    detail="Timeout renderizando HTML",
                ) from exc

            try:
                t_before_shot = time.monotonic()
                screenshot = await page.screenshot(
                    full_page=False,
                    type="png",
                    timeout=REQUEST_TIMEOUT,
                )
                t_after_shot = time.monotonic()
            except PlaywrightTimeoutError as exc:
                raise HTTPException(
                    status_code=408,
                    detail="Timeout tomando screenshot",
                ) from exc

            return screenshot
        finally:
            await context.close()
            if not shared:
                # Close the per-call browser/playwright
                try:
                    await browser.close()
                except Exception:
                    pass
                try:
                    await p.stop()
                except Exception:
                    pass
            end_total = time.monotonic()
            # Print phase timings (milliseconds)
            try:
                print(
                    f"[screenshot] total={(end_total-start_total)*1000:.0f}ms "
                    f"context={(t1-t0)*1000:.0f}ms "
                    f"set_content={(t_after_set-t_before_set)*1000:.0f}ms "
                    f"screenshot={(t_after_shot-t_before_shot)*1000:.0f}ms"
                )
            except Exception:
                # Best-effort logging; ignore if timing vars missing
                pass

    async def _capture_selector(
        self,
        html: str,
        selector: str,
    ) -> bytes | None:
        start_total = time.monotonic()
        p, browser, shared = await create_browser()

        t0 = time.monotonic()
        context = await browser.new_context(
            viewport={
                "width": SELECTOR_VIEWPORT_SIZE,
                "height": SELECTOR_VIEWPORT_SIZE,
            },
            java_script_enabled=False,
            device_scale_factor=DEVICE_SCALE_FACTOR,
        )
        t1 = time.monotonic()

        try:
            page = await context.new_page()

            await page.route("**/*", block_requests)

            try:
                t_before_set = time.monotonic()
                await page.set_content(
                    html,
                    wait_until="domcontentloaded",
                    timeout=REQUEST_TIMEOUT,
                )
                t_after_set = time.monotonic()
            except PlaywrightTimeoutError as exc:
                raise HTTPException(
                    status_code=408,
                    detail="Timeout renderizando HTML",
                ) from exc

            element = await page.query_selector(selector)
            if not element:
                return None

            try:
                t_before_shot = time.monotonic()
                result = await element.screenshot(
                    type="png",
                    scale="device",
                    timeout=REQUEST_TIMEOUT,
                )
                t_after_shot = time.monotonic()
            except PlaywrightTimeoutError as exc:
                raise HTTPException(
                    status_code=408,
                    detail="Timeout tomando screenshot",
                ) from exc

            return result
        finally:
            await context.close()
            if not shared:
                try:
                    await browser.close()
                except Exception:
                    pass
                try:
                    await p.stop()
                except Exception:
                    pass
            end_total = time.monotonic()
            try:
                print(
                    f"[screenshot-selector] total={(end_total-start_total)*1000:.0f}ms "
                    f"context={(t1-t0)*1000:.0f}ms "
                    f"set_content={(t_after_set-t_before_set)*1000:.0f}ms "
                    f"screenshot={(t_after_shot-t_before_shot)*1000:.0f}ms"
                )
            except Exception:
                pass