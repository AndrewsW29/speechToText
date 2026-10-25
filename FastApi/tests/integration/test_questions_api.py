from fastapi.testclient import TestClient

from tests.integration.conftest import WEBM


def _post(client: TestClient, content: bytes, content_type: str = "audio/webm") -> object:
    return client.post("/v1/questions", files={"audio": ("q.webm", content, content_type)})


def test_valid_audio_returns_transcript_and_answer(client: TestClient) -> None:
    response = _post(client, WEBM)
    assert response.status_code == 200  # type: ignore[attr-defined]
    body = response.json()  # type: ignore[attr-defined]
    assert body["transcript"]["text"]
    assert body["answer"]["text"]
    assert len(body["answer"]["sources"]) >= 1
    assert body["question_id"]


def test_empty_audio_is_422_problem_details(client: TestClient) -> None:
    response = _post(client, b"")
    assert response.status_code == 422  # type: ignore[attr-defined]
    assert response.headers["content-type"].startswith("application/problem+json")  # type: ignore[attr-defined]
    body = response.json()  # type: ignore[attr-defined]
    assert body["status"] == 422
    assert "traceback" not in str(body).lower()


def test_unsupported_content_is_415(client: TestClient) -> None:
    response = _post(client, b"not audio at all", "text/plain")
    assert response.status_code == 415  # type: ignore[attr-defined]


def test_declared_audio_with_wrong_bytes_is_415(client: TestClient) -> None:
    response = _post(client, b"MZ-this-is-an-exe" + b"\x00" * 32, "audio/webm")
    assert response.status_code == 415  # type: ignore[attr-defined]


def test_oversized_audio_is_413(client: TestClient) -> None:
    response = _post(client, WEBM + b"\x00" * 2048)
    assert response.status_code == 413  # type: ignore[attr-defined]


def test_missing_audio_field_is_422_problem_details(client: TestClient) -> None:
    response = client.post("/v1/questions", files={"other": ("x", b"y", "text/plain")})
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").status_code == 200
