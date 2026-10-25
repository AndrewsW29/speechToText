"""Noisy-channel correction: fix ASR spellings of technical terms from a curated glossary.

Pure application logic (rapidfuzz only). Matches are accepted best-score first and never
overlap, so a neighbouring word such as "a" cannot be swallowed by a longer, close-scoring phrase.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

import yaml
from rapidfuzz import fuzz, process

MAX_WORDS = 4


def _key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


class GlossaryCorrector:
    def __init__(self, terms: Mapping[str, str], cutoff: int = 90) -> None:
        """`terms` maps a normalized key (lowercase letters/digits) to the canonical spelling."""
        self._terms = dict(terms)
        self._keys = list(self._terms)
        self._cutoff = cutoff

    @classmethod
    def from_yaml(cls, path: Path, cutoff: int = 90) -> GlossaryCorrector:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        terms: dict[str, str] = {}
        for entry in data["terms"]:
            canonical = entry["canonical"]
            spellings = list(entry.get("aliases", []))
            if entry.get("match_canonical", True):
                spellings.insert(0, canonical)
            for spelling in spellings:
                terms[_key(spelling)] = canonical
        return cls(terms, cutoff)

    def correct(self, text: str) -> str:
        words = text.split()
        candidates: list[tuple[float, int, int, str]] = []
        for i in range(len(words)):
            for n in range(1, MAX_WORDS + 1):
                if i + n > len(words):
                    break
                phrase = _key("".join(words[i : i + n]))
                if not phrase:
                    continue
                hit = process.extractOne(
                    phrase, self._keys, scorer=fuzz.ratio, score_cutoff=self._cutoff
                )
                if hit:
                    candidates.append((hit[1], i, n, self._terms[hit[0]]))

        taken: set[int] = set()
        replace: dict[int, tuple[int, str]] = {}
        for _, i, n, term in sorted(candidates, key=lambda c: (-c[0], -c[2], c[1])):
            span = set(range(i, i + n))
            if not span & taken:
                taken |= span
                replace[i] = (n, term)

        out: list[str] = []
        i = 0
        while i < len(words):
            n, term = replace.get(i, (1, words[i]))
            out.append(term)
            i += n
        return " ".join(out)
