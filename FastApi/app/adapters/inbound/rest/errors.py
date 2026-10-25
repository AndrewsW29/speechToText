"""RFC 9457 Problem Details: one error shape, no internals leaked."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.adapters.outbound.ingestion.document_sources import UrlNotAllowedError
from app.application.errors import (
    InvalidAudioError,
    NoRelevantSourcesError,
    NotAPdfError,
    PixelBudgetExceededError,
    QueueUnavailableError,
    QuotaExceededError,
    TooLargeError,
    TooManyPagesError,
    TranscriptionError,
    UploadRejectedError,
)

PROBLEM_JSON = "application/problem+json"
logger = logging.getLogger(__name__)


class ProblemError(Exception):
    def __init__(self, status: int, title: str, detail: str | None = None) -> None:
        super().__init__(title)
        self.status = status
        self.title = title
        self.detail = detail


def problem_response(
    status: int, title: str, detail: str | None = None, **extra: Any
) -> JSONResponse:
    body: dict[str, Any] = {"type": "about:blank", "title": title, "status": status, **extra}
    if detail:
        body["detail"] = detail
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProblemError)
    async def _problem(_: Request, exc: ProblemError) -> JSONResponse:
        return problem_response(exc.status, exc.title, exc.detail)

    @app.exception_handler(InvalidAudioError)
    async def _invalid_audio(_: Request, exc: InvalidAudioError) -> JSONResponse:
        return problem_response(422, "Invalid audio", str(exc))

    @app.exception_handler(TranscriptionError)
    async def _transcription(_: Request, exc: TranscriptionError) -> JSONResponse:
        logger.warning("transcription failed: %s", exc)
        return problem_response(502, "Speech-to-text unavailable")

    @app.exception_handler(NoRelevantSourcesError)
    async def _no_sources(_: Request, exc: NoRelevantSourcesError) -> JSONResponse:
        return problem_response(
            404, "No relevant knowledge found", "Try rephrasing or ask about another topic"
        )

    @app.exception_handler(UrlNotAllowedError)
    async def _url_not_allowed(_: Request, exc: UrlNotAllowedError) -> JSONResponse:
        return problem_response(422, "URL not allowed", "The URL failed ingestion validation")

    @app.exception_handler(NotAPdfError)
    async def _not_a_pdf(_: Request, exc: NotAPdfError) -> JSONResponse:
        return problem_response(415, "Unsupported media type", str(exc))

    @app.exception_handler(TooLargeError)
    async def _too_large(_: Request, exc: TooLargeError) -> JSONResponse:
        return problem_response(413, "File too large", str(exc))

    @app.exception_handler(QuotaExceededError)
    async def _quota(_: Request, exc: QuotaExceededError) -> JSONResponse:
        return problem_response(429, "Quota exceeded", str(exc))

    @app.exception_handler(TooManyPagesError)
    @app.exception_handler(PixelBudgetExceededError)
    @app.exception_handler(UploadRejectedError)
    async def _rejected(_: Request, exc: UploadRejectedError) -> JSONResponse:
        return problem_response(422, "Upload rejected", str(exc))

    @app.exception_handler(QueueUnavailableError)
    async def _queue(_: Request, exc: QueueUnavailableError) -> JSONResponse:
        return problem_response(503, "Processing unavailable", str(exc))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = sorted(
            {".".join(str(p) for p in e["loc"][1:]) or str(e["loc"][0]) for e in exc.errors()}
        )
        return problem_response(422, "Validation failed", "Invalid request fields", fields=fields)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return problem_response(
            exc.status_code, str(exc.detail) if exc.status_code < 500 else "Error"
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error", exc_info=exc)
        return problem_response(500, "Internal server error")
