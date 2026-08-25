import pytest
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def mock_screenshot():
    with patch("app.api.routes.screenshot.service") as svc:
        svc.screenshot_selector = AsyncMock()
        yield svc


@pytest.mark.asyncio
async def test_returns_png(mock_screenshot):
    mock_screenshot.screenshot_selector.return_value = (b"\x89PNG\r\n\x1a\nfake", False)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/html-to-image/selector",
            json={"html": "<div class='tarjeta'></div>", "selector": ".tarjeta"},
        )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


@pytest.mark.asyncio
async def test_x_cache_miss(mock_screenshot):
    mock_screenshot.screenshot_selector.return_value = (b"\x89PNG", False)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/html-to-image/selector",
            json={"html": "<div class='tarjeta'></div>"},
        )
    assert resp.headers["x-cache"] == "MISS"


@pytest.mark.asyncio
async def test_x_cache_hit(mock_screenshot):
    mock_screenshot.screenshot_selector.return_value = (b"\x89PNG", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/html-to-image/selector",
            json={"html": "<div class='tarjeta'></div>"},
        )
    assert resp.headers["x-cache"] == "HIT"


@pytest.mark.asyncio
async def test_404_on_none(mock_screenshot):
    mock_screenshot.screenshot_selector.return_value = (None, False)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/html-to-image/selector",
            json={"html": "<div class='tarjeta'></div>"},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_413_on_oversized_html(mock_screenshot):
    big_html = "x" * 5_000_000
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/html-to-image/selector",
            json={"html": big_html},
        )
    assert resp.status_code == 413


@pytest.mark.asyncio
async def test_400_on_invalid_selector(mock_screenshot):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/html-to-image/selector",
            json={"html": "<div></div>", "selector": ".not-allowed"},
        )
    assert resp.status_code == 400
