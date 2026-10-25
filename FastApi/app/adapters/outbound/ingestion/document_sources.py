"""Document sources. The HTTP source is SSRF-hardened: allowlisted hosts, public IPs only,
no redirects, size cap."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable, Iterable
from html.parser import HTMLParser
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlparse

import httpx

from app.application.ports.document_source import DocumentSource
from app.domain.retrieval import Document

TEXT_SUFFIXES = {".md", ".txt", ".java", ".kt"}
CODE_SUFFIXES = {".java", ".kt"}


class UrlNotAllowedError(ValueError):
    """The URL failed validation or the response was unacceptable."""


def parse_front_matter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        return {}, raw.strip()
    head, _, body = raw[4:].partition("\n---\n")
    meta = {}
    for line in head.splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return meta, body.strip()


class LocalDirectorySource(DocumentSource):
    """Reads .md/.txt/.java/.kt files with optional `key: value` front matter."""

    def fetch(
        self, url: str, language: str = "java", framework: str | None = None
    ) -> list[Document]:
        root = Path(url)
        if not root.is_dir():
            raise ValueError(f"not a directory: {url}")
        documents = []
        for path in sorted(root.rglob("*")):
            if path.suffix not in TEXT_SUFFIXES or not path.is_file():
                continue
            meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
            documents.append(
                Document(
                    source_url=meta.get("source_url", path.as_uri()),
                    text=body,
                    language=meta.get("language", language),
                    framework=meta.get("framework", framework),
                    artifact_type=meta.get("artifact_type"),
                    content_type=meta.get(
                        "content_type", "code" if path.suffix in CODE_SUFFIXES else "text"
                    ),
                )
            )
        return documents


class _TextExtractor(HTMLParser):
    SKIP: ClassVar[frozenset[str]] = frozenset({"script", "style", "noscript", "template"})

    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag in self.SKIP:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip and data.strip():
            self.parts.append(data.strip())


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return " ".join(parser.parts)


def system_resolver(host: str) -> list[str]:
    return sorted({str(info[4][0]) for info in socket.getaddrinfo(host, None)})


class HttpDocumentSource(DocumentSource):
    def __init__(
        self,
        allowed_hosts: Iterable[str],
        client: httpx.Client | None = None,
        resolver: Callable[[str], list[str]] = system_resolver,
        max_bytes: int = 2 * 1024 * 1024,
    ) -> None:
        self._hosts = {h.lower() for h in allowed_hosts}
        self._client = client or httpx.Client(timeout=10.0, follow_redirects=False)
        self._resolver = resolver
        self._max_bytes = max_bytes

    def _validate(self, url: str) -> None:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
            raise UrlNotAllowedError("only plain http(s) URLs with a host are allowed")
        if host not in self._hosts:
            raise UrlNotAllowedError("host is not in the ingestion allowlist")
        for address in self._resolver(host):
            ip = ipaddress.ip_address(address)
            if not ip.is_global:
                raise UrlNotAllowedError("host resolves to a non-public address")

    def fetch(
        self, url: str, language: str = "java", framework: str | None = None
    ) -> list[Document]:
        self._validate(url)
        response = self._client.get(url)
        if response.is_redirect:
            raise UrlNotAllowedError("redirects are not followed")
        response.raise_for_status()
        if len(response.content) > self._max_bytes:
            raise UrlNotAllowedError("document exceeds the size limit")
        text = (
            html_to_text(response.text)
            if "html" in response.headers.get("content-type", "")
            else response.text
        )
        return [Document(source_url=url, text=text, language=language, framework=framework)]
