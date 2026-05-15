from fastapi import HTTPException

from app.core.config import (
    ALLOWED_SELECTORS,
    MAX_HEIGHT,
    MAX_HTML_SIZE,
    MAX_WIDTH,
)


def validate_html_size(html: str) -> None:
    size = len(html.encode("utf-8"))
    if size > MAX_HTML_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"HTML demasiado grande. Máximo: {MAX_HTML_SIZE} bytes",
        )


def clamp_dimensions(width: int, height: int) -> tuple[int, int]:
    width = max(1, min(width, MAX_WIDTH))
    height = max(1, min(height, MAX_HEIGHT))
    return width, height


def validate_selector(selector: str) -> None:
    if selector not in ALLOWED_SELECTORS:
        raise HTTPException(
            status_code=400,
            detail="Selector no permitido",
        )
