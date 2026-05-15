def is_allowed_request(url: str) -> bool:
    return url.startswith("data:")
