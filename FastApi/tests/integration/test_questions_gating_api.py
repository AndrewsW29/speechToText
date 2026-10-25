from app.adapters.outbound.answer.fixed_answer_generator import FixedAnswerGenerator
from app.application.use_cases.ask_question import AskQuestion
from app.config import Settings
from app.main import Container, create_app
from fastapi.testclient import TestClient

from tests.fakes import FakeClassifier, FakeTranscriber
from tests.integration.conftest import WEBM


def _post(classifier: FakeClassifier, **settings: object) -> dict:
    uc = AskQuestion(
        FakeTranscriber("create a controller"), FixedAnswerGenerator(), classifier=classifier
    )
    app = create_app(Settings(auth_enabled=False, **settings), container=Container(ask_question=uc))
    response = TestClient(app).post(
        "/v1/questions", files={"audio": ("q.webm", WEBM, "audio/webm")}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_answer_response_includes_the_detected_intent() -> None:
    body = _post(FakeClassifier("CREATE_CODE_ARTIFACT", 0.93, {"LANGUAGE": "java"}))
    assert body["status"] == "answer" and body["answer"]["sources"]
    assert body["intent"] == {
        "name": "CREATE_CODE_ARTIFACT",
        "confidence": 0.93,
        "entities": {"LANGUAGE": "java"},
    }
    assert body["clarification"] is None


def test_clarify_response_carries_a_question_and_option_chips() -> None:
    body = _post(FakeClassifier("CREATE_CODE_ARTIFACT", 0.95, {}))
    assert body["status"] == "clarify" and body["answer"] is None
    assert body["clarification"] == {
        "question": "Which language should I use?",
        "options": ["java", "kotlin", "typescript"],
    }
    assert body["transcript"]["text"]


def test_abstain_response_has_a_polite_message_and_no_answer() -> None:
    body = _post(FakeClassifier("OUT_OF_SCOPE", 0.99))
    assert body["status"] == "abstain" and body["answer"] is None and "outside" in body["message"]


def test_command_response_for_meta_intents() -> None:
    body = _post(FakeClassifier("META_COMMAND", 0.97))
    assert body["status"] == "command" and body["answer"] is None


def test_profile_default_language_makes_the_clarify_case_answerable() -> None:
    body = _post(FakeClassifier("CREATE_CODE_ARTIFACT", 0.95, {}), default_language="java")
    assert body["status"] == "answer" and body["intent"]["entities"]["LANGUAGE"] == "java"
