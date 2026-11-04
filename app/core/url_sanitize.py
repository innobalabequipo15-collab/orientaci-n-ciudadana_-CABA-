"""Sanitiza URLs de fuentes externas antes de exponerlas al cliente."""

from __future__ import annotations

from urllib.parse import urlparse


def sanitize_http_url(url: str | None) -> str | None:
    if not url or not isinstance(url, str):
        return None
    trimmed = url.strip()
    if not trimmed:
        return None
    try:
        parsed = urlparse(trimmed)
    except ValueError:
        return None
    if parsed.scheme not in ("http", "https"):
        return None
    if not parsed.netloc:
        return None
    return trimmed
