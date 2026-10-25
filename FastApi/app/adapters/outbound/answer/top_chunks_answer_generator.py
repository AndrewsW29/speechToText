"""Retrieval-only answer: the best chunks, each cited as a source (no LLM yet; see US4)."""

from collections.abc import Sequence
from urllib.parse import urlparse

from app.application.errors import NoRelevantSourcesError
from app.application.ports.answer_generator import AnswerGenerator
from app.domain.entities import Answer, Query, Source
from app.domain.retrieval import ScoredChunk

MAX_STEPS = 3
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


class TopChunksAnswerGenerator(AnswerGenerator):
    def generate(self, query: Query, chunks: Sequence[ScoredChunk] = ()) -> Answer:
        top = list(chunks)[:MAX_STEPS]
        if not top:
            raise NoRelevantSourcesError("no chunks to answer from")
        text = "\n\n".join(f"{i}. {hit.chunk.text}" for i, hit in enumerate(top, start=1))
        sources = tuple(
            Source(id=hit.chunk.id, title=_title(hit), url=hit.chunk.source_url, kind=_kind(hit))
            for hit in top
        )
        return Answer(text=text, sources=sources)
