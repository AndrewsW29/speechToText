from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from uuid import uuid4

from app.application.errors import ClassificationError, InvalidAudioError, NoRelevantSourcesError
from app.application.ports.answer_generator import AnswerGenerator
from app.application.ports.intent_classifier import IntentClassifier
from app.application.ports.transcriber import Transcriber
from app.application.services.intent_router import IntentRouter, default_router
from app.application.services.retriever import Retriever
from app.domain.confidence_gate import ConfidenceGate, Decision
from app.domain.entities import Answer, Intent, Query
from app.domain.retrieval import ScoredChunk, SearchFilters

logger = logging.getLogger(__name__)

LANGUAGE_OPTIONS = ["java", "kotlin", "typescript"]
KNOWN_LANGUAGES = frozenset({"java", "kotlin", "python", "typescript", "swift", "go"})
OUT_OF_SCOPE_MESSAGE = "That's outside what I can help with. Ask me about software development."
LOW_CONFIDENCE_MESSAGE = "I'm not sure I understood. Could you rephrase that?"


@dataclass(frozen=True, slots=True)
class Clarification:
    question: str
    options: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AskQuestionResult:
    """status: answer | clarify | abstain | command."""

    query: Query
    answer: Answer | None = None
    status: str = "answer"
    intent: Intent | None = None
    clarification: Clarification | None = None
    message: str | None = None


class AskQuestion:
    """Inbound use case: audio in; an answer, a question back, a refusal or a command out.

    Depends only on ports. Without a classifier it behaves as the plain retrieval pipeline.
    """

    def __init__(
        self,
        transcriber: Transcriber,
        generator: AnswerGenerator,
        retriever: Retriever | None = None,
        classifier: IntentClassifier | None = None,
        gate: ConfidenceGate | None = None,
        router: IntentRouter | None = None,
    ) -> None:
        self._transcriber = transcriber
        self._generator = generator
        self._retriever = retriever
        self._classifier = classifier
        self._gate = gate or ConfidenceGate()
        self._router = router or default_router()

    def execute(
        self,
        audio: bytes,
        language: str | None = None,
        profile: Mapping[str, str] | None = None,
    ) -> AskQuestionResult:
        if not audio:
            raise InvalidAudioError("audio payload is empty")
        transcript = self._transcriber.transcribe(audio, language)
        query = Query(id=uuid4().hex, transcript=transcript)

        intent = self._classify(transcript.text, profile)
        if intent is None:  # no classifier, or it is down: ungated pipeline
            return self._answer(query, None, None)

        decision = self._gate.decide(intent)
        if decision is Decision.ABSTAIN:
            message = (
                OUT_OF_SCOPE_MESSAGE if intent.name == "OUT_OF_SCOPE" else LOW_CONFIDENCE_MESSAGE
            )
            return AskQuestionResult(query, status="abstain", intent=intent, message=message)
        if decision is Decision.CLARIFY:
            return AskQuestionResult(
                query, status="clarify", intent=intent, clarification=self._clarification(intent)
            )

        handler = self._router.route(intent)
        if not handler.needs_retrieval:
            return AskQuestionResult(
                query, status="command", intent=intent, message=transcript.text
            )
        return self._answer(query, intent, self._filters(intent))

    def _classify(self, text: str, profile: Mapping[str, str] | None) -> Intent | None:
        if self._classifier is None:
            return None
        try:
            intent = self._classifier.classify(text)
        except ClassificationError:
            logger.warning("intent classifier unavailable; continuing without the confidence gate")
            return None
        merged = {**(profile or {}), **intent.entities}  # spoken entities beat profile defaults
        return Intent(intent.name, intent.confidence, merged)

    def _clarification(self, intent: Intent) -> Clarification:
        if "LANGUAGE" in self._gate.missing_entities(intent):
            return Clarification("Which language should I use?", list(LANGUAGE_OPTIONS))
        return Clarification("Can you tell me a bit more about what you need?")

    @staticmethod
    def _filters(intent: Intent) -> SearchFilters:
        """Language is a hard filter (only when recognised); framework and version are ranking
        features for the reranker (US11), so they never exclude results here."""
        language = intent.entities.get("LANGUAGE", "").strip().lower()
        return SearchFilters(language=language if language in KNOWN_LANGUAGES else None)

    def _answer(
        self, query: Query, intent: Intent | None, filters: SearchFilters | None
    ) -> AskQuestionResult:
        chunks: list[ScoredChunk] = []
        if self._retriever is not None:
            chunks = self._retriever.retrieve(query.transcript.text, filters)
            if not chunks:
                raise NoRelevantSourcesError("no relevant knowledge found for this question")
        answer = self._generator.generate(query, chunks)
        return AskQuestionResult(query, answer=answer, intent=intent)
