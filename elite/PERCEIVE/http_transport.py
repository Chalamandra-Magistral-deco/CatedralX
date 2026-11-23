"""Shared standard-library HTTPS transport with redirects disabled."""
from __future__ import annotations

import math
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _NoRedirectHandler(HTTPRedirectHandler):
    """Prevent HTTP clients from following a server-controlled redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def open_no_redirect_request(request: Request, *, timeout: float = 10.0):
    """Open one HTTPS request without following redirects."""
    if not isinstance(request, Request):
        raise TypeError("request must be urllib.request.Request")
    try:
        timeout_value = float(timeout)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("timeout must be a positive finite number") from exc
    if isinstance(timeout, bool) or not math.isfinite(timeout_value) or timeout_value <= 0:
        raise ValueError("timeout must be a positive finite number")
    if urlsplit(request.full_url).scheme.lower() != "https":
        raise ValueError("only HTTPS destinations are allowed")
    opener = build_opener(_NoRedirectHandler)
    return opener.open(request, timeout=timeout_value)
