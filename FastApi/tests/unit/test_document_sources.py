from pathlib import Path

import httpx
import pytest
from app.adapters.outbound.ingestion.document_sources import (
    HttpDocumentSource,
    LocalDirectorySource,
    UrlNotAllowedError,
)

MD = "---\nsource_url: https://docs.example/a\nlanguage: java\nframework: spring\nartifact_type: service\n---\nBody text here.\n"
JAVA = "---\nsource_url: https://x/UserService.java\nlanguage: java\ncontent_type: code\n---\nclass A { }\n"


def test_local_source_reads_front_matter(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text(MD)
    (tmp_path / "B.java").write_text(JAVA)
    (tmp_path / "ignored.bin").write_bytes(b"\x00\x01")
    docs = {d.source_url: d for d in LocalDirectorySource().fetch(str(tmp_path))}
    assert set(docs) == {"https://docs.example/a", "https://x/UserService.java"}
    a = docs["https://docs.example/a"]
    assert (a.language, a.framework, a.artifact_type, a.content_type) == (
        "java",
        "spring",
        "service",
        "text",
    )
    assert a.text == "Body text here."
    assert docs["https://x/UserService.java"].content_type == "code"


def test_local_source_requires_existing_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        LocalDirectorySource().fetch(str(tmp_path / "missing"))


def _http(
    handler, hosts=("docs.example",), resolver=lambda host: ["93.184.216.34"]
) -> HttpDocumentSource:  # type: ignore[no-untyped-def]
    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)
    return HttpDocumentSource(allowed_hosts=hosts, client=client, resolver=resolver, max_bytes=1000)


def test_http_source_fetches_and_strips_html() -> None:
    html = "<html><head><style>x{}</style></head><body><h1>Title</h1><script>evil()</script><p>Use a Service.</p></body></html>"
    src = _http(lambda r: httpx.Response(200, text=html, headers={"content-type": "text/html"}))
    [doc] = src.fetch("https://docs.example/page", "java", "spring")
    assert "Title" in doc.text and "Use a Service." in doc.text
    assert "evil" not in doc.text and "x{}" not in doc.text
    assert (doc.source_url, doc.language, doc.framework) == (
        "https://docs.example/page",
        "java",
        "spring",
    )


@pytest.mark.parametrize(
    "url",
    [
        "ftp://docs.example/x",
        "file:///etc/passwd",
        "https://evil.example/x",
        "https:///nohost",
        "https://user@docs.example.evil/x",
    ],
)
def test_http_source_rejects_bad_urls(url: str) -> None:
    with pytest.raises(UrlNotAllowedError):
        _http(lambda r: httpx.Response(200, text="x")).fetch(url)


@pytest.mark.parametrize(
    "ip", ["127.0.0.1", "10.0.0.5", "169.254.169.254", "192.168.1.1", "::1", "172.16.0.9"]
)
def test_http_source_blocks_private_addresses(ip: str) -> None:
    src = _http(lambda r: httpx.Response(200, text="x"), resolver=lambda host: [ip])
    with pytest.raises(UrlNotAllowedError):
        src.fetch("https://docs.example/x")


def test_http_source_does_not_follow_redirects() -> None:
    src = _http(lambda r: httpx.Response(302, headers={"location": "http://169.254.169.254/"}))
    with pytest.raises(UrlNotAllowedError):
        src.fetch("https://docs.example/x")


def test_http_source_enforces_size_limit() -> None:
    src = _http(lambda r: httpx.Response(200, text="a" * 5000))
    with pytest.raises(UrlNotAllowedError):
        src.fetch("https://docs.example/x")
