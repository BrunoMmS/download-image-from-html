from fastapi import APIRouter, Form
from fastapi.responses import Response

from app.services.screenshot_service import ScreenshotService
from app.utils.validators import (
    clamp_dimensions,
    validate_html_size,
    validate_selector,
)

router = APIRouter()
service = ScreenshotService()


@router.post("/html-to-image")
async def html_to_image(
    html: str = Form(...),
    width: int = Form(default=800),
    height: int = Form(default=800),
):
    validate_html_size(html)
    width, height = clamp_dimensions(width, height)
    screenshot = await service.screenshot_page(html, width, height)
    return Response(
        content=screenshot,
        media_type="image/png",
        headers={
            "Content-Disposition": "attachment; filename=image.png"
        },
    )


@router.post("/html-to-image/selector")
async def html_to_image_selector(
    html: str = Form(...),
    selector: str = Form(default=".tarjeta"),
):
    validate_html_size(html)
    validate_selector(selector)
    screenshot = await service.screenshot_selector(html, selector)
    if screenshot is None:
        return Response(
            content=b"Selector no encontrado",
            status_code=404,
        )
    return Response(
        content=screenshot,
        media_type="image/png",
        headers={
            "Content-Disposition": "attachment; filename=selector.png"
        },
    )
