import logging
import time

from fastapi import Request

logger = logging.getLogger("app.access")


async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)

    logger.info(
        "%s %s %s %d %.1fms %s",
        request.client.host,
        request.method,
        request.url.path,
        response.status_code,
        duration,
        response.headers.get("content-length", "-"),
    )

    return response
