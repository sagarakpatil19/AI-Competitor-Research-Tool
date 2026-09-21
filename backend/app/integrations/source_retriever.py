from __future__ import annotations

import hashlib
import ipaddress
import re
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Protocol
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx


MAX_RESPONSE_SIZE = 5 * 1024 * 1024
MAX_REDIRECTS = 5
MAX_EXCERPT_LENGTH = 1000


class RetrievalError(Exception):
    def __init__(self, category: str, reason: str, http_status: int | None = None) -> None:
        super().__init__(reason)
        self.category = category
        self.reason = reason
        self.http_status = http_status


@dataclass(frozen=True)
class RetrievedSource:
    final_url: str
    http_status: int
    content_type: str
    content: str
    content_excerpt: str
    content_hash: str
    retrieved_at: datetime
    source_title: str | None = None
    publisher: str | None = None


class SourceRetriever(Protocol):
    def retrieve(self, url: str) -> RetrievedSource:
        ...


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self._ignored_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "template", "head"}:
            self._ignored_depth += 1
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
        if tag.lower() in {"script", "style", "noscript", "template", "head"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if not self._ignored_depth:
            self.parts.append(data)


def canonicalize_url(url: str) -> str:
    try:
        parsed = urlsplit(url.strip())
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid source URL") from exc
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are supported")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Invalid source URL")
    hostname = parsed.hostname.lower()
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    if port is not None and not ((parsed.scheme.lower() == "http" and port == 80) or (parsed.scheme.lower() == "https" and port == 443)):
        hostname = f"{hostname}:{port}"
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme.lower(), hostname, path, parsed.query, ""))


def _is_unsafe_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved or ip.is_unspecified or ip.is_multicast


def validate_destination(url: str, resolve_hostname: bool = True) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise RetrievalError("unsupported_scheme", "Only HTTP and HTTPS URLs are supported")
    try:
        try:
            ipaddress.ip_address(parsed.hostname)
            addresses = {parsed.hostname}
        except ValueError:
            if resolve_hostname:
                addresses = {
                    result[4][0]
                    for result in socket.getaddrinfo(
                        parsed.hostname,
                        parsed.port or (443 if parsed.scheme == "https" else 80),
                        type=socket.SOCK_STREAM,
                    )
                }
            else:
                addresses = {parsed.hostname}
        if any(_is_unsafe_ip(address) for address in addresses):
            raise RetrievalError("unsafe_destination", "Source destination is not allowed")
    except ValueError:
        raise RetrievalError("invalid_url", "Invalid source URL") from None
    except socket.gaierror:
        raise RetrievalError("dns_failure", "Source hostname could not be resolved") from None


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_content(body: bytes, content_type: str) -> tuple[str, str | None]:
    try:
        text = body.decode("utf-8", errors="replace")
        if content_type == "text/html":
            parser = _VisibleTextParser()
            parser.feed(text)
            return _normalize_text(" ".join(parser.parts)), _normalize_text(" ".join(parser.title_parts)) or None
        return _normalize_text(text), None
    except Exception as exc:
        raise RetrievalError("extraction_failure", "Source content could not be extracted") from exc


class HttpxSourceRetriever:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client

    def retrieve(self, url: str) -> RetrievedSource:
        current_url = canonicalize_url(url)
        timeout = httpx.Timeout(10.0, connect=5.0, read=10.0, write=10.0, pool=5.0)
        client = self.client or httpx.Client(timeout=timeout, follow_redirects=False)
        close_client = self.client is None
        try:
            for _ in range(MAX_REDIRECTS + 1):
                validate_destination(current_url)
                with client.stream("GET", current_url) as response:
                    if 300 <= response.status_code < 400:
                        location = response.headers.get("location")
                        if not location:
                            raise RetrievalError("redirect_failure", "Redirect did not provide a destination", response.status_code)
                        try:
                            current_url = canonicalize_url(urljoin(current_url, location))
                        except ValueError as exc:
                            raise RetrievalError("redirect_failure", "Redirect destination is invalid", response.status_code) from exc
                        continue

                    if response.status_code >= 400:
                        category = "http_4xx" if response.status_code < 500 else "http_5xx"
                        raise RetrievalError(category, f"Source returned HTTP {response.status_code}", response.status_code)

                    if response.status_code == 204:
                        content = ""
                        content_type = "text/plain"
                        title = None
                    else:
                        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                        if content_type not in {"text/html", "text/plain"}:
                            raise RetrievalError("unsupported_content_type", "Source content type is not supported", response.status_code)
                        content_length = response.headers.get("content-length")
                        if content_length:
                            try:
                                if int(content_length) > MAX_RESPONSE_SIZE:
                                    raise RetrievalError("response_too_large", "Source response is too large", response.status_code)
                            except ValueError as exc:
                                raise RetrievalError("response_too_large", "Source response size is invalid", response.status_code) from exc
                        body_parts: list[bytes] = []
                        body_size = 0
                        for chunk in response.iter_bytes():
                            body_size += len(chunk)
                            if body_size > MAX_RESPONSE_SIZE:
                                raise RetrievalError("response_too_large", "Source response is too large", response.status_code)
                            body_parts.append(chunk)
                        content, title = extract_content(b"".join(body_parts), content_type)

                if response.status_code != 204 and not content:
                    raise RetrievalError("extraction_failure", "Source contained no extractable content", response.status_code)
                retrieved_at = datetime.now(timezone.utc)
                return RetrievedSource(
                    final_url=current_url,
                    http_status=response.status_code,
                    content_type=content_type,
                    content=content,
                    content_excerpt=content[:MAX_EXCERPT_LENGTH],
                    content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    retrieved_at=retrieved_at,
                    source_title=title,
                )
            raise RetrievalError("redirect_failure", "Too many redirects")
        except RetrievalError:
            raise
        except httpx.TimeoutException as exc:
            raise RetrievalError("timeout", "Source request timed out") from exc
        except httpx.ConnectError as exc:
            raise RetrievalError("connection_failure", "Could not connect to source") from exc
        except httpx.TransportError as exc:
            raise RetrievalError("connection_failure", "Source request failed") from exc
        finally:
            if close_client:
                client.close()