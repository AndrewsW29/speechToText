import pytest
from app.adapters.outbound.answer.fixed_answer_generator import FixedAnswerGenerator
from app.application.use_cases.ask_question import AskQuestion
from app.config import Settings
from app.main import Container, create_app
from fastapi.testclient import TestClient

from tests.fakes import FakeTranscriber

WEBM = b"\x1a\x45\xdf\xa3" + b"\x00" * 64  # EBML header => WebM/Matroska


@pytest.fixture
def settings() -> Settings:
    return Settings(auth_enabled=False, max_audio_bytes=1024)


@pytest.fixture
def client(settings: Settings) -> TestClient:
    container = Container(
        ask_question=AskQuestion(transcriber=FakeTranscriber(), generator=FixedAnswerGenerator())
    )
    return TestClient(create_app(settings, container=container))
