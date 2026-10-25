"""Intent router: a cheap classifier result picks the handler; heavy parts only run when needed."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from app.domain.entities import Intent


@dataclass(frozen=True, slots=True)
class Handler:
    name: str
    needs_retrieval: bool


class IntentRouter:
    def __init__(self, handlers: Mapping[str, Handler], fallback: Handler) -> None:
        self._handlers = dict(handlers)
        self._fallback = fallback

    def route(self, intent: Intent) -> Handler:
        return self._handlers.get(intent.name, self._fallback)


def default_router() -> IntentRouter:
    """Handler names mirror ml/data/taxonomy.yaml (one handler per intent)."""
    return IntentRouter(
        {
            "CREATE_CODE_ARTIFACT": Handler("create_code", True),
            "EXPLAIN_CONCEPT": Handler("explain", True),
            "FIND_DOCS": Handler("find_docs", True),
            "DEBUG_ERROR": Handler("debug", True),
            "COMPARE_OPTIONS": Handler("compare", True),
            "MODIFY_PREVIOUS": Handler("modify", True),
            "META_COMMAND": Handler("meta", False),
            "OUT_OF_SCOPE": Handler("refuse", False),
        },
        fallback=Handler("explain", True),
    )
