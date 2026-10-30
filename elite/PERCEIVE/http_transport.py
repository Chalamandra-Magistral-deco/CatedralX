"""Shared standard-library HTTP transport with redirects disabled."""
from __future__ import annotations

from urllib.request import HTTPRedirectHandler, Request, build_opener


class _NoRedirectHandler(HTTPRedirectHandler):
    """Prevent HTTP clients from following a server-controlled redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def open_no_redirect_request(request: Request, *, timeout: float = 10.0):
    """Open one HTTP request without following redirects.

    A 3xx response is surfaced as ``HTTPError`` by urllib instead of connecting
    to its Location. Callers must set a finite timeout and handle HTTP errors.
    """
    opener = build_opener(_NoRedirectHandler)
    return opener.open(request, timeout=timeout)
