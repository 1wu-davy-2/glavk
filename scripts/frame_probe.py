#!/usr/bin/env python
"""探测目标系统能否被 glavk 用 iframe 内嵌（只读诊断，不改任何数据）。

对每个地址发一次请求读响应头，判断三件事：

1. X-Frame-Options / CSP frame-ancestors —— 是否禁止被其他站点嵌套。
   命中 DENY / SAMEORIGIN / frame-ancestors 'none'|'self' 时，iframe 里
   只会是空白页。这是浏览器强制执行的，前端没有任何绕过手段。
2. 协议 —— glavk 走 HTTPS 时，http:// 目标会被混合内容策略直接拦截。
3. 会话 cookie 的 SameSite —— Lax/Strict（或没写，现代浏览器按 Lax 处理）
   在跨站 iframe 里不会被发送，症状是「在 iframe 里登录成功，翻一页就掉登录」。

只打印 cookie 的属性，不打印 cookie 的值；URL 回显时去掉 userinfo 和查询串。

用法：
    python scripts/frame_probe.py https://a.example.com http://10.0.0.5:8080
    python scripts/frame_probe.py --insecure https://self-signed.example.com
    python scripts/frame_probe.py --from-db ./data/glavk.sqlite3

依赖 httpx（已在 backend/requirements.txt 里）。
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import httpx


TIMEOUT_SECONDS = 10.0
# HEAD 被拒时退回 GET 的状态码
HEAD_REJECTED_STATUSES = {400, 403, 405, 501}


def display_url(url: str) -> str:
    """回显用：去掉 userinfo 和查询串，避免把凭据打进终端。"""
    parts = urlsplit(url)
    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"
    return urlunsplit((parts.scheme, host, parts.path, "", ""))


def urls_from_db(path: str) -> list[str]:
    """只取 web_projects.url 一列，不碰 username / password_ciphertext。"""
    database = Path(path).expanduser()
    if not database.is_file():
        raise SystemExit(f"数据库不存在：{database}")
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        rows = connection.execute("SELECT url FROM web_projects ORDER BY sort_order, name").fetchall()
    finally:
        connection.close()
    return [row[0] for row in rows if row[0]]


def fetch_headers(client: httpx.Client, url: str) -> tuple[httpx.Response | None, str | None]:
    """先试 HEAD，被拒就退回 GET；两种都只读响应头，不下载正文。"""
    last_error: str | None = None
    for method in ("HEAD", "GET"):
        try:
            request = client.build_request(method, url)
            response = client.send(request, stream=True)
            response.close()
        except httpx.HTTPError as error:
            last_error = f"{type(error).__name__}: {error}"
            continue
        if method == "HEAD" and response.status_code in HEAD_REJECTED_STATUSES:
            continue
        return response, None
    return None, last_error


def frame_ancestors_values(csp_headers: list[str]) -> list[str]:
    """从所有 CSP 头里抽出 frame-ancestors 指令的值。"""
    found: list[str] = []
    for header in csp_headers:
        for directive in header.split(";"):
            parts = directive.strip().split()
            if parts and parts[0].lower() == "frame-ancestors":
                found.append(" ".join(parts[1:]) or "(空)")
    return found


def judge_embeddable(response: httpx.Response) -> tuple[bool, str]:
    """返回 (是否禁止嵌入, 说明)。CSP frame-ancestors 存在时浏览器忽略 X-Frame-Options。"""
    ancestors = frame_ancestors_values(response.headers.get_list("content-security-policy"))
    if ancestors:
        joined = " / ".join(ancestors)
        tokens = {token.lower() for value in ancestors for token in value.split()}
        if "'none'" in tokens:
            return True, f"CSP frame-ancestors 'none' —— 明确禁止被嵌套（{joined}）"
        if "'self'" in tokens:
            return True, f"CSP frame-ancestors 'self' —— 只允许同源嵌套，glavk 跨域会被挡（{joined}）"
        if "*" in tokens:
            return False, f"CSP frame-ancestors 允许任意来源（{joined}）"
        return False, f"CSP frame-ancestors 限定了来源，需确认里面包含 glavk 的地址（{joined}）"

    xfo_values = [value.strip().upper() for value in response.headers.get_list("x-frame-options")]
    if not xfo_values:
        return False, "没有 X-Frame-Options，也没有 CSP frame-ancestors —— 可以嵌入"
    for value in xfo_values:
        if value.startswith("DENY"):
            return True, "X-Frame-Options: DENY —— 明确禁止被嵌套"
        if value.startswith("SAMEORIGIN"):
            return True, "X-Frame-Options: SAMEORIGIN —— 只允许同源嵌套，glavk 跨域会被挡"
    return False, f"X-Frame-Options: {' / '.join(xfo_values)} —— 现代浏览器已忽略 ALLOW-FROM，实际不拦截"


def cookie_same_site(response: httpx.Response) -> tuple[str, str]:
    """返回 (结论标签, 说明)。只看属性，不打印 cookie 的值。"""
    cookies = response.headers.get_list("set-cookie")
    if not cookies:
        return "无 cookie", "首个响应没下发 cookie；会话 cookie 通常在登录后才出现，登录后再测一次更准"

    values: list[str] = []
    for cookie in cookies:
        for part in cookie.split(";")[1:]:
            key, _, raw = part.strip().partition("=")
            if key.strip().lower() == "samesite":
                values.append(raw.strip().lower() or "?")

    if not values:
        return "未设置", "没写 SameSite —— 现代浏览器按 Lax 处理，跨站 iframe 里不会发送，大概率掉登录"
    if all(value == "none" for value in values):
        if all("secure" in cookie.lower() for cookie in cookies):
            return "None", "SameSite=None + Secure —— 跨站 iframe 可以带 cookie，但仍受浏览器第三方 cookie 策略影响"
        return "None（缺 Secure）", "SameSite=None 但没配 Secure，浏览器会直接拒绝这个 cookie"
    return " / ".join(sorted(set(values))), "SameSite 不是 None —— 跨站 iframe 里不会发送，登录后翻页会掉"


@dataclass
class Result:
    url: str
    reachable: bool = False
    status: int | None = None
    final_url: str = ""
    redirected_host: bool = False
    blocked: bool = False
    frame_reason: str = ""
    scheme_note: str = ""
    cookie_label: str = ""
    cookie_note: str = ""
    error: str = ""


def probe(client: httpx.Client, url: str) -> Result:
    result = Result(url=url)
    response, error = fetch_headers(client, url)
    if response is None:
        result.error = error or "请求失败"
        return result

    result.reachable = True
    result.status = response.status_code
    result.final_url = display_url(str(response.url))
    result.redirected_host = urlsplit(result.final_url).hostname != urlsplit(url).hostname
    result.blocked, result.frame_reason = judge_embeddable(response)

    if urlsplit(str(response.url)).scheme == "http":
        result.scheme_note = "目标是 HTTP —— 如果 glavk 自己走 HTTPS，这个 iframe 会被混合内容策略拦掉"
    else:
        result.scheme_note = "目标是 HTTPS —— 与 glavk 同协议时不受混合内容限制"

    result.cookie_label, result.cookie_note = cookie_same_site(response)
    return result


def report(results: list[Result]) -> None:
    for index, result in enumerate(results, start=1):
        print(f"\n[{index}/{len(results)}] {display_url(result.url)}")
        if not result.reachable:
            print(f"  ✗ 无法访问：{result.error}")
            continue
        print(f"  状态：{result.status}   最终地址：{result.final_url}")
        if result.redirected_host:
            print("  注意：跳转到了不同的主机，iframe 里会停在跳转后的页面")
        print(f"  嵌套：{'✗ 被禁止' if result.blocked else '✓ 允许'} —— {result.frame_reason}")
        print(f"  协议：{result.scheme_note}")
        print(f"  会话 cookie：{result.cookie_label} —— {result.cookie_note}")

    reachable = [item for item in results if item.reachable]
    embeddable = [item for item in reachable if not item.blocked]
    cookie_ok = [item for item in embeddable if item.cookie_label == "None"]

    print("\n" + "=" * 60)
    print(f"可访问 {len(reachable)}/{len(results)}，其中允许被嵌套 {len(embeddable)} 个")
    if embeddable:
        print(f"  嵌套 + 会话 cookie 都过关的：{len(cookie_ok)} 个")
        if cookie_ok:
            for item in cookie_ok:
                print(f"    ✓ {display_url(item.url)}")
        print("  注意：即使两项都过关，Chrome/Safari 的第三方 cookie 策略仍可能在真实使用中拦截会话，")
        print("        建议拿其中一个手工在 iframe 里走一遍完整登录流程再下结论。")
    else:
        print("  没有目标允许被嵌套 —— iframe 方案在当前这批系统上不可行，建议只做「打开面板」。")
    print("=" * 60)


def force_utf8_output() -> None:
    """Windows 控制台默认按 GBK 编码输出，中文和 ✓/✗ 会直接抛 UnicodeEncodeError。

    终端显示乱码时执行 `chcp 65001` 切到 UTF-8 代码页。
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    force_utf8_output()
    parser = argparse.ArgumentParser(description="探测目标系统能否被 iframe 内嵌")
    parser.add_argument("urls", nargs="*", help="要探测的地址，可以给多个")
    parser.add_argument("--from-db", metavar="PATH", help="从 glavk 的 SQLite 库里读项目地址（只读 url 列）")
    parser.add_argument("--insecure", action="store_true", help="跳过 TLS 证书校验，用于自签名证书的内网系统")
    args = parser.parse_args()

    urls = list(args.urls)
    if args.from_db:
        urls.extend(urls_from_db(args.from_db))
    if not urls:
        parser.print_help()
        raise SystemExit("\n错误：至少给一个地址，或者用 --from-db 指定数据库。")

    # 去重但保持顺序
    unique_urls = list(dict.fromkeys(urls))

    with httpx.Client(
        follow_redirects=True,
        timeout=TIMEOUT_SECONDS,
        verify=not args.insecure,
        headers={"User-Agent": "glavk-frame-probe/1.0"},
    ) as client:
        results = [probe(client, url) for url in unique_urls]

    report(results)


if __name__ == "__main__":
    sys.exit(main())
