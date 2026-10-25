from __future__ import annotations

from collections.abc import Sequence


def decode_entities(tokens: Sequence[str], tags: Sequence[str]) -> dict[str, str]:
    """BIO tags -> {LABEL: text}; first span per label wins; dangling I- tags are ignored."""
    entities: dict[str, str] = {}
    label: str | None = None
    words: list[str] = []

    def flush() -> None:
        nonlocal label, words
        if label is not None and label not in entities:
            entities[label] = " ".join(words)
        label, words = None, []

    for token, tag in zip(tokens, tags, strict=False):
        if tag.startswith("B-"):
            flush()
            label, words = tag[2:], [token]
        elif tag.startswith("I-") and label == tag[2:]:
            words.append(token)
        else:
            flush()
    flush()
    return entities
