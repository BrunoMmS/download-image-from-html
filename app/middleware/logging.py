import time

from fastapi import Request


async def log_requests(request: Request, call_next):
    start = time.time()

    """if request.url.path == "/html-to-image/selector":
        form = await request.form()
        html = form.get("html", "")

        print(f"HTML SIZE: {len(html.encode('utf-8'))} bytes")
    """
    response = await call_next(request)

    duration = round((time.time() - start) * 1000, 2)

    print(
        f"[{request.client.host}] "
        f"{request.method} "
        f"{request.url.path} "
        f"{response.status_code} "
        f"{duration}ms "
        f"{response.headers.get('content-length', '-')}b"
    )

    return response
