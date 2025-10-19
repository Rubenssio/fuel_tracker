from __future__ import annotations

from urllib.parse import parse_qsl, unquote, urlencode, urlparse

_ALLOWED_NEXT_PATHS = {"/", "/vehicles", "/history", "/metrics", "/settings"}


def sanitize_next(raw: str | None, default: str = "/") -> str:
    """Return a safe relative path for redirect targets."""
    if not raw:
        return default

    value = raw
    for _ in range(3):
        decoded = unquote(value)
        if decoded == value:
            break
        value = decoded

    parsed = urlparse(value)
    path = parsed.path or ""

    if not path.startswith("/"):
        return default
    if path not in _ALLOWED_NEXT_PATHS:
        return default

    if not parsed.query:
        return path

    cleaned_params = [
        (key, val)
        for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if key != "next"
    ]
    if not cleaned_params:
        return path

    querystring = urlencode(cleaned_params, doseq=True)
    return f"{path}?{querystring}" if querystring else path
