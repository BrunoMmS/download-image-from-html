import sys

from fastapi import APIRouter

from app.schemas.responses import HealthResponse
from app.services.screenshot_service import ScreenshotService
from app.utils.playwright_runner import _BROWSER

router = APIRouter()
service = ScreenshotService()


@router.get("/health", response_model=HealthResponse)
async def health():
    browser_mode = "singleton" if _BROWSER is not None else "per-request"
    if sys.platform == "win32":
        browser_mode = "per-request"

    return HealthResponse(
        status="ok",
        browser=browser_mode,
        cache=service._cache.stats,
    )
