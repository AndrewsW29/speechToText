"""Inline entity markup -> JSONL records.

`make a [spring boot|FRAMEWORK] [service|ARTIFACT] in [java|LANGUAGE]` becomes lowercase tokens
with BIO tags. Punctuation is dropped from tokens.
"""

from __future__ import annotations

import re

LABELS = frozenset({"LANGUAGE", "FRAMEWORK", "ARTIFACT", "LIBRARY", "VERSION", "ERROR_CODE"})
_ENTITY = re.compile(r"\[([^\]|\[]+)\|([A-Z_]+)\]")
_TOKEN = re.compile(r"\.?[\w@+#]+(?:[.\-/][\w@+#]+)*")


class MarkupError(ValueError):
    pass


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def parse_markup(text: str) -> tuple[list[str], list[str]]:
    tokens: list[str] = []
    tags: list[str] = []
    pos = 0

    def plain(chunk: str) -> None:
        if "[" in chunk or "]" in chunk:
            raise MarkupError(f"unbalanced or malformed brackets in: {text!r}")
        found = tokenize(chunk)
        tokens.extend(found)
        tags.extend("O" for _ in found)

    for match in _ENTITY.finditer(text):
        plain(text[pos : match.start()])
        label = match.group(2)
        if label not in LABELS:
            raise MarkupError(f"unknown entity label {label!r}")
        words = tokenize(match.group(1))
        if not words:
            raise MarkupError(f"empty entity in: {text!r}")
        tokens.extend(words)
        tags.extend([f"B-{label}"] + [f"I-{label}"] * (len(words) - 1))
        pos = match.end()
    plain(text[pos:])
    return tokens, tags


def to_record(record_id: str, intent: str, markup: str, source: str) -> dict[str, object]:
    tokens, tags = parse_markup(markup)
    return {"id": record_id, "tokens": tokens, "tags": tags, "intent": intent, "source": source}
