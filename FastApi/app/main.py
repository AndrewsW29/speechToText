"""Composition root: the only place that knows the concrete adapters."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.adapters.inbound.rest import ingestions, questions
from app.adapters.inbound.rest.auth import jwks_verifier
from app.adapters.inbound.rest.errors import register_error_handlers
from app.adapters.inbound.rest.health import build_health_router
from app.adapters.inbound.rest.observability import install_observability
from app.adapters.outbound.answer.fixed_answer_generator import FixedAnswerGenerator
from app.adapters.outbound.answer.top_chunks_answer_generator import TopChunksAnswerGenerator
from app.adapters.outbound.ingestion.celery_jobs import CeleryIngestionJobs
from app.adapters.outbound.ingestion.inline_jobs import InlineIngestionJobs
from app.adapters.outbound.intent.tf_serving_classifier import (
    ModelMeta,
    TFServingIntentClassifier,
)
from app.adapters.outbound.stt.factory import TranscriberFactory
from app.adapters.outbound.stt.glossary_corrected_transcriber import GlossaryCorrectedTranscriber
from app.application.ports.ingestion_jobs import IngestionJobs
from app.application.ports.intent_classifier import IntentClassifier
from app.application.services.glossary import GlossaryCorrector
from app.application.use_cases.ask_question import AskQuestion
from app.bootstrap import build_ingestion_facade, build_retriever
from app.config import Settings, get_settings
from app.container import Container

__all__ = ["Container", "create_app"]


def _build_ingestion(settings: Settings) -> IngestionJobs:
    if settings.ingestion_backend == "celery":
        from app.workers.celery_app import celery_app
        from app.workers.ingestion_tasks import register_default_tasks

        return CeleryIngestionJobs(register_default_tasks(), celery_app)
    return InlineIngestionJobs(
        build_ingestion_facade(settings, allow_local=settings.environment == "local")
    )


def _build_classifier(settings: Settings) -> IntentClassifier | None:
    if settings.intent_serving_url is None or settings.intent_model_dir is None:
        return None
    return TFServingIntentClassifier(
        httpx.Client(base_url=settings.intent_serving_url, timeout=2.0),
        settings.intent_model_name,
        ModelMeta.load(settings.intent_model_dir),
        settings.intent_model_label,
    )


def build_container(settings: Settings) -> Container:
    """Without VA_QDRANT_URL the API serves the fixed walking-skeleton answer (US1)."""
    transcriber = TranscriberFactory.create(settings)
    if settings.glossary_path is not None:
        transcriber = GlossaryCorrectedTranscriber(
            transcriber, GlossaryCorrector.from_yaml(settings.glossary_path)
        )
    if settings.qdrant_url is None:
        return Container(ask_question=AskQuestion(transcriber, FixedAnswerGenerator()))
    return Container(
        ask_question=AskQuestion(
            transcriber,
            TopChunksAnswerGenerator(),
            build_retriever(settings),
            _build_classifier(settings),
        ),
        ingestion=_build_ingestion(settings),
    )


def create_app(settings: Settings | None = None, *, container: Container | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = container or build_container(settings)
        yield

    app = FastAPI(title="Voice Dev Assistant API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    if container is not None:  # tests may use the client without running lifespan
        app.state.container = container
    app.state.verifier = jwks_verifier(settings) if settings.auth_enabled else None

    install_observability(
        app, service_name=settings.otel_service_name, log_level=settings.log_level
    )
    register_error_handlers(app)
    app.include_router(build_health_router())
    app.include_router(questions.router)
    app.include_router(ingestions.router)
    return app
