"""Chunking strategies (Strategy pattern). Pure functions of text, no I/O."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod


class Chunker(ABC):
    @abstractmethod
    def chunk(self, text: str) -> list[str]: ...


class SentenceChunker(Chunker):
    """Greedily packs whole sentences up to max_chars; an oversized sentence stays whole."""

    def __init__(self, max_chars: int = 800) -> None:
        if max_chars <= 0:
            raise ValueError("max_chars must be positive")
        self._max = max_chars

    def chunk(self, text: str) -> list[str]:
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            candidate = f"{current} {sentence}".strip()
            if current and len(candidate) > self._max:
                chunks.append(current)
                current = sentence
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks


class TokenChunker(Chunker):
    """Sliding window over whitespace tokens with overlap."""

    def __init__(self, max_tokens: int = 200, overlap: int = 20) -> None:
        if max_tokens <= 0 or not 0 <= overlap < max_tokens:
            raise ValueError("need max_tokens > 0 and 0 <= overlap < max_tokens")
        self._max, self._overlap = max_tokens, overlap

    def chunk(self, text: str) -> list[str]:
        words = text.split()
        chunks: list[str] = []
        start, step = 0, self._max - self._overlap
        while start < len(words):
            chunks.append(" ".join(words[start : start + self._max]))
            if start + self._max >= len(words):
                break
            start += step
        return chunks


_CLASS_DECL = re.compile(
    r"^[ \t]*(?:(?:public|protected|private|abstract|final|static|sealed)\s+)*"
    r"(?:class|interface|enum|record)\s+\w+",
    re.MULTILINE,
)


def _skip_literal(text: str, i: int) -> int:
    """Return the index after a string/char literal or comment starting at i (or i if none)."""
    if text.startswith("//", i):
        end = text.find("\n", i)
        return len(text) if end == -1 else end
    if text.startswith("/*", i):
        end = text.find("*/", i + 2)
        return len(text) if end == -1 else end + 2
    if text[i] in "\"'":
        quote, j = text[i], i + 1
        while j < len(text) and text[j] != quote:
            j += 2 if text[j] == "\\" else 1
        return j + 1
    return i


def _matching_brace(text: str, open_idx: int) -> int:
    depth, i = 0, open_idx
    while i < len(text):
        skipped = _skip_literal(text, i)
        if skipped != i:
            i = skipped
            continue
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(text) - 1


def _members(body: str) -> list[str]:
    """Split a class body into top-level members (fields, constructors, methods, nested types)."""
    members: list[str] = []
    depth, start, i = 0, 0, 0
    while i < len(body):
        skipped = _skip_literal(body, i)
        if skipped != i:
            i = skipped
            continue
        ch = body[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                members.append(body[start : i + 1].strip())
                start = i + 1
        elif ch == ";" and depth == 0:
            members.append(body[start : i + 1].strip())
            start = i + 1
        i += 1
    return [m for m in members if m]


class CodeAwareChunker(Chunker):
    """Splits Java-like source per method; each chunk repeats the class header so it stands alone.

    Consecutive field declarations are grouped into one chunk. Braces stay balanced per chunk.
    """

    def chunk(self, text: str) -> list[str]:
        chunks: list[str] = []
        pos = 0
        while (match := _CLASS_DECL.search(text, pos)) is not None:
            open_idx = text.find("{", match.end())
            if open_idx == -1:
                break
            close_idx = _matching_brace(text, open_idx)
            header = self._header(text, match.start(), open_idx)
            chunks.extend(self._class_chunks(header, text[open_idx + 1 : close_idx]))
            pos = close_idx + 1
        return chunks or ([text.strip()] if text.strip() else [])

    @staticmethod
    def _header(text: str, decl_start: int, open_idx: int) -> str:
        lines_before = text[:decl_start].rstrip("\n").split("\n")
        annotations: list[str] = []
        while lines_before and lines_before[-1].strip().startswith("@"):
            annotations.insert(0, lines_before.pop().strip())
        declaration = text[decl_start:open_idx].strip()
        return "\n".join([*annotations, f"{declaration} {{"])

    @staticmethod
    def _class_chunks(header: str, body: str) -> list[str]:
        pending_fields: list[str] = []
        out: list[str] = []

        def wrap(parts: list[str]) -> str:
            indented = "\n\n".join("  " + p.replace("\n", "\n  ") for p in parts)
            return f"{header}\n{indented}\n}}"

        for member in _members(body):
            if "{" not in member:
                pending_fields.append(member)
                continue
            parts = [*pending_fields, member] if pending_fields else [member]
            out.append(wrap(parts))
            pending_fields = []
        if pending_fields:
            out.append(wrap(pending_fields))
        return out
