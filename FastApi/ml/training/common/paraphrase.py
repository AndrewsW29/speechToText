"""LLM paraphrasing through a local Ollama server, plus the human-review sample export."""

from __future__ import annotations

import random
import re
from collections.abc import Mapping, Sequence
from typing import Any

import httpx

_BULLET = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s*")
PROMPT = (
    "Rewrite the developer request below in {n} different ways a person might say it aloud. "
    "Keep the meaning and every technical term. One per line, no commentary.\n\nRequest: {text}"
)


class OllamaParaphraser:
    def __init__(self, client: httpx.Client, model: str) -> None:
        self._client = client
        self._model = model

    def paraphrase(self, text: str, n: int = 5) -> list[str]:
        try:
            response = self._client.post(
                "/api/generate",
                json={
                    "model": self._model,
                    "prompt": PROMPT.format(n=n, text=text),
                    "stream": False,
                },
            )
            response.raise_for_status()
            raw = str(response.json().get("response", ""))
        except (httpx.HTTPError, ValueError):
            return []
        seen = {text.strip().lower()}
        out: list[str] = []
        for line in raw.splitlines():
            candidate = _BULLET.sub("", line).strip()
            if len(candidate.split()) < 3 or candidate.lower() in seen:
                continue
            seen.add(candidate.lower())
            out.append(candidate)
        return out[:n]


def review_sample(
    rows: Sequence[Mapping[str, Any]], fraction: float, seed: int
) -> list[dict[str, Any]]:
    """Deterministic sample (e.g. 10-20%) shaped as Label Studio tasks for human review."""
    count = round(len(rows) * fraction)
    chosen = random.Random(seed).sample(list(rows), count)
    return [
        {
            "data": {"text": " ".join(r["tokens"]), "intent": r["intent"]},
            "meta": {"id": r["id"], "source": r.get("source")},
        }
        for r in chosen
    ]


def synthetic_share(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    """Per-intent share of rows that are not hand-written seed data."""
    totals: dict[str, list[int]] = {}
    for row in rows:
        counts = totals.setdefault(row["intent"], [0, 0])
        counts[0] += 1
        counts[1] += row.get("source") not in {"seed", "golden", "production"}
    return {intent: synthetic / total for intent, (total, synthetic) in totals.items()}
