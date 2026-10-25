"""Scrub PII and secrets before text enters any dataset."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Finding:
    kind: str
    start: int
    end: int


_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("jwt", re.compile(r"eyJ[\w-]+\.[\w-]+\.[\w-]+")),
    ("aws_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("api_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    ("ip_address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    (
        "spoken_secret",
        re.compile(
            r"\b(?:password|passcode|api key|secret|token)\s+(?:is|equals|=)\s+(?!\[REDACTED)[^.\n]+",
            re.IGNORECASE,
        ),
    ),
]
_SPOKEN_HEAD = re.compile(r"(.*?\b(?:is|equals|=))\s+", re.IGNORECASE)


def scrub(text: str) -> tuple[str, list[Finding]]:
    findings: list[Finding] = []
    for kind, pattern in _PATTERNS:

        def replace(match: re.Match[str], kind: str = kind) -> str:
            findings.append(Finding(kind, match.start(), match.end()))
            if kind == "spoken_secret":
                head = _SPOKEN_HEAD.match(match.group(0))
                return f"{head.group(1) if head else ''} [REDACTED:{kind}]"
            return f"[REDACTED:{kind}]"

        text = pattern.sub(replace, text)
    return text, findings
