"""Turns retrieved chunks (and optionally generated text) into a sourced Answer."""

from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import urlparse

from app.application.errors import NoRelevantSourcesError
from app.domain.entities import Answer, Source
from app.domain.retrieval import ScoredChunk

REPOSITORY_HOSTS = ("github.com", "gitlab.com", "bitbucket.org")


def _kind(hit: ScoredChunk) -> str:
    host = urlparse(hit.chunk.source_url or "").netloc.lower()
    return "repository" if host.endswith(REPOSITORY_HOSTS) else "documentation"


def _title(hit: ScoredChunk) -> str:
    url = hit.chunk.source_url
    if url:
        parsed = urlparse(url)
        tail = parsed.path.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").replace("_", " ")
        return f"{parsed.netloc}: {tail}".strip(": ") if tail else parsed.netloc
    return hit.chunk.text[:60]


class AnswerBuilder:
    def __init__(self, max_sources: int = 3) -> None:
        self._max_sources = max_sources

    def build(self, text: str, chunks: Sequence[ScoredChunk]) -> Answer:
        top = list(chunks)[: self._max_sources]
        if not top:
            raise NoRelevantSourcesError("no chunks to answer from")
        return Answer(
            text=text,
            sources=tuple(
                Source(id=h.chunk.id, title=_title(h), url=h.chunk.source_url, kind=_kind(h))
                for h in top
            ),
            confidence=min(1.0, max(0.0, top[0].score)),
            snippets=tuple(h.chunk.text for h in top),
        )

    def top(self, chunks: Sequence[ScoredChunk]) -> list[ScoredChunk]:
        return list(chunks)[: self._max_sources]
