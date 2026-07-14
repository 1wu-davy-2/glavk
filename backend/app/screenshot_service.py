from __future__ import annotations

import ipaddress
import re
import socket
from pathlib import Path
from urllib.parse import urlparse

from .config import Settings


class ScreenshotTargetError(ValueError):
    """Raised when a screenshot target is not safe to request."""


class ScreenshotService:
    def __init__(self, settings: Settings):
        self._root = Path(settings.screenshot_dir).expanduser().resolve()
        self._allow_private_networks = settings.screenshot_allow_private_networks
        self._timeout_ms = 8_000

    @property
    def root(self) -> Path:
        return self._root

    def validate_target(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ScreenshotTargetError("截图地址必须是有效的 HTTP 或 HTTPS 地址")
        if parsed.username or parsed.password:
            raise ScreenshotTargetError("截图地址不能包含登录凭据")
        try:
            parsed.port
        except ValueError as error:
            raise ScreenshotTargetError("截图地址端口无效") from error
        if self._allow_private_networks:
            return

        hostname = parsed.hostname
        try:
            addresses = {ipaddress.ip_address(hostname)}
        except ValueError:
            try:
                addresses = {
                    ipaddress.ip_address(info[4][0])
                    for info in socket.getaddrinfo(hostname, parsed.port or 80, type=socket.SOCK_STREAM)
                }
            except socket.gaierror as error:
                raise ScreenshotTargetError("截图地址无法解析") from error
        if not addresses or any(self._is_private_address(address) for address in addresses):
            raise ScreenshotTargetError("截图地址指向受限制的网络")

    @staticmethod
    def _is_private_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        return any(
            (
                address.is_private,
                address.is_loopback,
                address.is_link_local,
                address.is_reserved,
                address.is_multicast,
                address.is_unspecified,
            )
        )

    def resolve_path(self, relative_path: str) -> Path:
        root = self._root
        candidate = (root / relative_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ValueError("截图路径越界") from error
        return candidate

    def capture(self, project_id: str, url: str) -> str:
        self.validate_target(url)
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", project_id):
            raise ValueError("项目编号无效")
        output = self.resolve_path(f"{project_id}.png")
        output.parent.mkdir(parents=True, exist_ok=True)

        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--no-sandbox"],
            )
            context = browser.new_context(viewport={"width": 1280, "height": 720})
            page = context.new_page()
            page.set_default_navigation_timeout(self._timeout_ms)
            page.route("**/*", self._handle_route)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=self._timeout_ms)
                page.screenshot(path=str(output), full_page=False, type="png")
            finally:
                context.close()
                browser.close()
        return output.relative_to(self._root).as_posix()

    def _handle_route(self, route) -> None:
        request_url = route.request.url
        scheme = urlparse(request_url).scheme.lower()
        if scheme in {"data", "blob", "about"}:
            route.continue_()
            return
        try:
            self.validate_target(request_url)
        except ScreenshotTargetError:
            route.abort()
            return
        route.continue_()

    def delete(self, relative_path: str | None) -> None:
        if not relative_path:
            return
        try:
            self.resolve_path(relative_path).unlink(missing_ok=True)
        except (OSError, ValueError):
            return
