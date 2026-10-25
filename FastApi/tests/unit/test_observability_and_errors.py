import json
import logging

from app.adapters.inbound.rest.observability import JsonFormatter, correlation_id
from app.adapters.outbound.answer.fixed_answer_generator import FixedAnswerGenerator
from app.application.errors import TranscriptionError
from app.application.ports.transcriber import Transcriber
from app.application.use_cases.ask_question import AskQuestion
from app.config import Settings
from app.main import Container, create_app
from fastapi.testclient import TestClient

from tests.integration.conftest import WEBM


class Boom(Transcriber):
    def transcribe(self, audio: bytes, language: str | None = None):  # type: ignore[no-untyped-def]
        raise TranscriptionError("secret engine detail")


class Crash(Transcriber):
    def transcribe(self, audio: bytes, language: str | None = None):  # type: ignore[no-untyped-def]
        raise RuntimeError("SELECT * FROM secrets")


def _client(t: Transcriber) -> TestClient:
    c = Container(ask_question=AskQuestion(t, FixedAnswerGenerator()))
    return TestClient(
        create_app(Settings(auth_enabled=False), container=c), raise_server_exceptions=False
    )


def test_correlation_id_is_echoed_and_generated() -> None:
    client = _client(Boom())
    assert (
        client.get("/health/live", headers={"X-Correlation-ID": "abc"}).headers["X-Correlation-ID"]
        == "abc"
    )
    assert client.get("/health/live").headers["X-Correlation-ID"]


def test_transcription_failure_is_502_without_internals() -> None:
    r = _client(Boom()).post("/v1/questions", files={"audio": ("q", WEBM, "audio/webm")})
    assert r.status_code == 502
    assert "secret engine detail" not in r.text


def test_unhandled_error_is_generic_500_without_sql() -> None:
    r = _client(Crash()).post("/v1/questions", files={"audio": ("q", WEBM, "audio/webm")})
    assert r.status_code == 500
    assert "SELECT" not in r.text
    assert r.headers["content-type"].startswith("application/problem+json")


def test_unknown_route_is_problem_json_404() -> None:
    r = _client(Boom()).get("/nope")
    assert r.status_code == 404 and r.headers["content-type"].startswith("application/problem+json")


def test_json_formatter_includes_correlation_id() -> None:
    token = correlation_id.set("cid-1")
    try:
        record = logging.LogRecord("t", logging.INFO, __file__, 1, "hello %s", ("x",), None)
        data = json.loads(JsonFormatter().format(record))
    finally:
        correlation_id.reset(token)
    assert data["message"] == "hello x" and data["correlation_id"] == "cid-1"
