"""Domain entities and business rules. No framework or I/O imports."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from app.domain.value_objects import Confidence, Transcript

_VOTES = frozenset({"up", "down"})
SOURCE_KINDS = frozenset({"documentation", "article", "repository"})


@dataclass(frozen=True, slots=True)
class Source:
    id: str
    title: str
    url: str | None = None
    kind: str = "documentation"

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.title.strip():
            raise ValueError("source needs an id and a title")
        if self.kind not in SOURCE_KINDS:
            raise ValueError(f"source kind must be one of {sorted(SOURCE_KINDS)}")


@dataclass(frozen=True, slots=True)
class Query:
    id: str
    transcript: Transcript

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("query id must not be empty")


@dataclass(frozen=True, slots=True)
class Intent:
    name: str
    confidence: Confidence
    entities: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("intent name must not be empty")
        object.__setattr__(self, "entities", MappingProxyType(dict(self.entities)))


@dataclass(frozen=True, slots=True)
class KnowledgeChunk:
    id: str
    text: str
    language: str
    framework: str | None = None
    artifact_type: str | None = None
    source_url: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.text.strip():
            raise ValueError("chunk needs an id and text")


@dataclass(frozen=True, slots=True)
class Answer:
    """An answer can never exist without at least one source."""

    text: str
    sources: tuple[Source, ...]

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("answer text must not be empty")
        if not self.sources:
            raise ValueError("answer requires at least one source")


@dataclass(frozen=True, slots=True)
class Feedback:
    question_id: str
    vote: str
    reason: str | None = None
    consent_training: bool = False

    def __post_init__(self) -> None:
        if self.vote not in _VOTES:
            raise ValueError(f"vote must be one of {sorted(_VOTES)}")
