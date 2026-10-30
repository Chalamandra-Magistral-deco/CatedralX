"""Security regression tests for the shared no-redirect HTTP transport."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request

import pytest
from PERCEIVE.http_transport import open_no_redirect_request


class _RedirectHandler(BaseHTTPRequestHandler):
    target_hits = 0

    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/target")
            self.end_headers()
            return
        if self.path == "/target":
            type(self).target_hits += 1
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"unexpected redirect followed")
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *_args):
        pass


def test_transport_rejects_redirect_without_requesting_location():
    _RedirectHandler.target_hits = 0
    server = HTTPServer(("127.0.0.1", 0), _RedirectHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(f"http://127.0.0.1:{server.server_port}/redirect")
        with pytest.raises(HTTPError) as error:
            open_no_redirect_request(request, timeout=2.0)
        assert error.value.code == 302
        assert _RedirectHandler.target_hits == 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)
