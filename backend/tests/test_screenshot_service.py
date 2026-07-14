from __future__ import annotations

from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from backend.app.config import Settings
from backend.app.screenshot_service import ScreenshotService, ScreenshotTargetError


def make_service(tmp_path: Path, *, allow_private: bool = False) -> ScreenshotService:
    return ScreenshotService(
        Settings(
            screenshot_dir=str(tmp_path / "screenshots"),
            screenshot_allow_private_networks=allow_private,
        )
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://10.0.0.5",
        "http://[::1]/",
        "file:///etc/passwd",
    ],
)
def test_rejects_private_or_non_http_targets_by_default(tmp_path: Path, url: str):
    service = make_service(tmp_path)

    with pytest.raises(ScreenshotTargetError):
        service.validate_target(url)


def test_private_targets_can_be_explicitly_allowed_for_trusted_networks(tmp_path: Path):
    service = make_service(tmp_path, allow_private=True)

    service.validate_target("http://127.0.0.1:8080")


def test_resolve_path_rejects_paths_outside_screenshot_directory(tmp_path: Path):
    service = make_service(tmp_path)

    with pytest.raises(ValueError):
        service.resolve_path("../credentials.txt")


def test_captures_a_public_page_to_a_png_file(tmp_path: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = b"<html><body><h1>glavk</h1></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        service = make_service(tmp_path, allow_private=True)
        relative_path = service.capture("project-1", f"http://127.0.0.1:{server.server_port}")
        image = service.resolve_path(relative_path)
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert image.is_file()
    assert image.read_bytes().startswith(b"\x89PNG")
