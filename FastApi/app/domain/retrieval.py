"""Retrieval value types. Pure domain: no framework imports."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.domain.entities import KnowledgeChunk
from app.domain.value_objects import Embedding


@dataclass(frozen=True, slots=True)
class SearchFilters:
    """Payload filters derived from the question (entities as filters)."""

    language: str | None = None
    framework: str | None = None
    artifact_type: str | None = None


@dataclass(frozen=True, slots=True)
class ScoredChunk:
    chunk: KnowledgeChunk
    score: float


@dataclass(frozen=True, slots=True)
class IndexedChunk:
    chunk: KnowledgeChunk
    embedding: Embedding


@dataclass(frozen=True, slots=True)
class Document:
    source_url: str
    text: str
    language: str
    framework: str | None = None
    artifact_type: str | None = None
    content_type: str = "text"  # "text" or "code"


def chunk_id(source_url: str, text: str) -> str:
    """Idempotent id: the same source and content always hash to the same id."""
    normalized = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(f"{source_url}\n{normalized}".encode()).hexdigest()[:32]


_LANGUAGES = {
    "java": "java",
    "kotlin": "kotlin",
    "python": "python",
    "typescript": "typescript",
    "swift": "swift",
}


def extract_filters(question: str) -> SearchFilters:
    """Naive keyword entity extraction; replaced by the intent/slot model in US3."""
    words = set(re.findall(r"[a-z]+", question.lower()))
    language = next((value for key, value in _LANGUAGES.items() if key in words), None)
    framework = "spring" if "spring" in words else None
    return SearchFilters(language=language, framework=framework)
