"""Immutable value objects. Pure Python: no framework imports (hexagonal domain)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Language:
    code: str

    def __post_init__(self) -> None:
        code = self.code.strip().lower()
        if not code or len(code) > 10:
            raise ValueError(f"invalid language code: {self.code!r}")
        object.__setattr__(self, "code", code)


@dataclass(frozen=True, slots=True)
class Transcript:
    text: str
    language: Language | None = None

    def __post_init__(self) -> None:
        text = self.text.strip()
        if not text:
            raise ValueError("transcript text must not be empty")
        object.__setattr__(self, "text", text)


@dataclass(frozen=True, slots=True)
class Embedding:
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("embedding must not be empty")

    @property
    def dimension(self) -> int:
        return len(self.values)


@dataclass(frozen=True, slots=True)
class Confidence:
    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("confidence must be within [0, 1]")
