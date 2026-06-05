from fastapi import APIRouter, Response
from app.schemas.requests import HTMLRenderRequest
from app.services.screenshot_service import ScreenshotService
from app.utils.validators import (
    clamp_dimensions,
    validate_html_size,
    validate_selector,
)

router = APIRouter()
service = ScreenshotService()

@router.post("/html-to-image/selector")
async def html_to_image_selector(request: HTMLRenderRequest): 
    selector = request.selector or ".tarjeta"
    
    validate_html_size(request.html)
    validate_selector(selector)
    
    screenshot = await service.screenshot_selector(request.html, selector)
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