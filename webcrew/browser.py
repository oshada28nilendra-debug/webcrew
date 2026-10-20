"""Real Chromium DOM observations; exact-page, bounded and address-pinned read transport."""

import ipaddress
import os
import socket
from html.parser import HTMLParser
from datetime import datetime, timezone
from urllib.parse import urlsplit

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from .core import Error, digest
from .httpio import DeadlineHTTP, read_exchange


class _NavigationPolicy(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == "meta" and any(
            k == "http-equiv" and v and v.strip().casefold() == "refresh" for k, v in attrs
        ):
            raise Error("Automatic HTML navigation is unsupported")


def resolve(task):
    addresses = {}
    for url in task.allowed_urls:
        u = urlsplit(url)
        if u.hostname in addresses:
            continue
        if task.demo and u.hostname == "127.0.0.1":
            addresses[u.hostname] = "127.0.0.1"
            continue
        try:
            records = socket.getaddrinfo(u.hostname, 443, type=socket.SOCK_STREAM)
            ips = {r[4][0] for r in records}
            if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
                raise Error("Approved hostname resolves to a non-public address")
            addresses[u.hostname] = sorted(ips, key=lambda ip: ":" in ip)[0]
        except (OSError, UnicodeError):
            raise Error("Approved page DNS resolution failed") from None
    return addresses


class Browser:
    def __init__(self, task):
        self.task = task
        self.pw = self.browser = self.context = None
        self.blocked = []
        self.failure = None
        self.source_hash = None

    def __enter__(self):
        self.addresses = resolve(self.task)
        try:
            self.pw = sync_playwright().start()
            executable = os.environ.get("WEBCREW_CHROMIUM")
            self.browser = self.pw.chromium.launch(
                headless=True, **({"executable_path": executable} if executable else {})
            )
            self.context = self.browser.new_context(
                java_script_enabled=False,
                accept_downloads=False,
                service_workers="block",
                extra_http_headers={"DNT": "1"},
            )
            self.context.route("**/*", self._route)
            self.page = self.context.new_page()
            return self
        except PlaywrightError:
            self.__exit__()
            raise Error(
                "Cannot launch Chromium; install the documented browser dependency"
            ) from None

    def _route(self, route):
        request = route.request
        if (
            request.method != "GET"
            or request.resource_type != "document"
            or request.url not in self.task.allowed_urls
            or request.frame != self.page.main_frame
            or request.url != self.expected_url
            or self.document_requested
        ):
            self.blocked.append(
                {"url": request.url[:2000], "method": request.method, "reason": "Request policy"}
            )
            self.failure = "Browser attempted an unapproved request"
            route.abort()
            return
        try:
            self.document_requested = True
            u = urlsplit(request.url)
            conn = DeadlineHTTP(
                u.hostname,
                u.port or (443 if u.scheme == "https" else 80),
                15,
                tls=u.scheme == "https",
                ip=self.addresses[u.hostname],
            )
            status, headers, body = read_exchange(
                conn,
                "GET",
                u.path or "/",
                {"User-Agent": "WebCrew/0.1 read-only audit", "Accept": "text/html"},
                timeout=15,
                max_bytes=1_000_000,
            )
            if status != 200 or "text/html" not in headers.get("content-type", "").lower():
                raise Error(
                    "Page must return HTTP 200 HTML; redirects and downloads are unsupported"
                )
            html_text = body.decode("utf-8")
            parser = _NavigationPolicy()
            parser.feed(html_text)
            parser.close()
            import hashlib

            self.source_hash = hashlib.sha256(body).hexdigest()
            route.fulfill(
                status=200,
                body=body,
                headers={
                    "Content-Type": "text/html; charset=utf-8",
                    "Content-Security-Policy": "default-src 'none'; script-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'",
                    "Referrer-Policy": "no-referrer",
                },
            )
        except (Error, UnicodeError, PlaywrightError):
            self.failure = (
                "Approved page fetch failed, exceeded limits or returned unsupported content"
            )
            route.abort()

    def read(self, url):
        if url not in self.task.allowed_urls:
            raise Error("Navigation URL is not approved")
        self.failure = None
        self.source_hash = None
        self.expected_url = url
        self.document_requested = False
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            if self.failure or self.page.url != url or self.source_hash is None:
                raise Error(
                    self.failure or "Observed document URL does not match the approved read"
                )
            raw = self.page.locator("body").inner_text(timeout=5000)
            if len(raw.encode("utf-8")) > 24_000:
                raise Error("Rendered text exceeds the 24 KB observation budget")
            lines = list(dict.fromkeys(s.strip() for s in raw.splitlines() if s.strip()))
            if len(lines) > 80 or any(len(line) > 2000 for line in lines):
                raise Error("Rendered passages exceed observation limits")
            passages = [{"id": f"p{i}", "text": line} for i, line in enumerate(lines)]
            links = []
            for anchor in self.page.locator("a[href]").all()[:100]:
                href = anchor.evaluate("a => a.href")
                if (
                    href in self.task.allowed_urls
                    and href != url
                    and not any(item["url"] == href for item in links)
                ):
                    links.append(
                        {"id": f"l{len(links)}", "url": href, "text": anchor.inner_text()[:200]}
                    )
            return {
                "url": url,
                "title": self.page.title()[:200],
                "passages": passages,
                "links": links,
                "sha256": digest(passages),
                "html_sha256": self.source_hash,
                "observed_at": datetime.now(timezone.utc).isoformat(),
                "browser_version": self.browser.version,
            }
        except PlaywrightError:
            raise Error(self.failure or "Browser navigation or observation timed out") from None

    def __exit__(self, *_):
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.pw:
            self.pw.stop()
            self.pw = None
