import time
from typing import Any

import jwt
import pytest
from app.adapters.inbound.rest.auth import JwtVerifier
from app.adapters.inbound.rest.errors import ProblemError
from app.adapters.outbound.answer.fixed_answer_generator import FixedAnswerGenerator
from app.application.use_cases.ask_question import AskQuestion
from app.config import Settings
from app.main import Container, create_app
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from tests.fakes import FakeTranscriber
from tests.integration.conftest import WEBM

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ISS, AUD = "https://idp.test/realms/va", "voice-api"


def _token(**over: Any) -> str:
    claims: dict[str, Any] = {"sub": "u1", "iss": ISS, "aud": AUD, "exp": int(time.time()) + 60}
    claims.update(over)
    return jwt.encode(claims, KEY, algorithm="RS256")


def _verifier() -> JwtVerifier:
    return JwtVerifier(issuer=ISS, audience=AUD, key_resolver=lambda _t: KEY.public_key())


def test_valid_token_yields_principal() -> None:
    assert _verifier().verify(_token()).subject == "u1"


@pytest.mark.parametrize("over", [{"exp": 1}, {"aud": "other"}, {"iss": "https://evil"}])
def test_invalid_tokens_are_rejected(over: dict[str, Any]) -> None:
    with pytest.raises(ProblemError) as err:
        _verifier().verify(_token(**over))
    assert err.value.status == 401


def test_garbage_token_is_rejected() -> None:
    with pytest.raises(ProblemError):
        _verifier().verify("not-a-jwt")


def _secured_client() -> TestClient:
    app = create_app(
        Settings(
            auth_enabled=True,
            oidc_issuer=ISS,
            oidc_jwks_url="http://127.0.0.1:9/jwks",
            oidc_audience=AUD,
        ),
        container=Container(ask_question=AskQuestion(FakeTranscriber(), FixedAnswerGenerator())),
    )
    app.state.verifier = _verifier()
    return TestClient(app)


def test_endpoint_requires_bearer_token() -> None:
    files = {"audio": ("q.webm", WEBM, "audio/webm")}
    client = _secured_client()
    assert client.post("/v1/questions", files=files).status_code == 401
    ok = client.post("/v1/questions", files=files, headers={"Authorization": f"Bearer {_token()}"})
    assert ok.status_code == 200


def test_auth_enabled_without_oidc_settings_fails_fast() -> None:
    with pytest.raises(RuntimeError):
        create_app(Settings(auth_enabled=True))


def test_role_guard_requires_ingest_role() -> None:
    from app.adapters.inbound.rest.auth import Principal, has_role

    assert has_role(Principal("u", {"realm_access": {"roles": ["ingest"]}}), "ingest")
    assert not has_role(Principal("u", {"realm_access": {"roles": ["user"]}}), "ingest")
    assert not has_role(Principal("u", {}), "ingest")


def test_ingestion_endpoint_forbidden_without_role() -> None:
    from app.adapters.outbound.ingestion.inline_jobs import InlineIngestionJobs

    class NoopFacade:
        def ingest(self, url: str, language: str = "java", framework: str | None = None):  # type: ignore[no-untyped-def]
            raise AssertionError("must not be reached")

    app = create_app(
        Settings(
            auth_enabled=True,
            oidc_issuer=ISS,
            oidc_jwks_url="http://127.0.0.1:9/jwks",
            oidc_audience=AUD,
        ),
        container=Container(
            ask_question=AskQuestion(FakeTranscriber(), FixedAnswerGenerator()),
            ingestion=InlineIngestionJobs(NoopFacade()),  # type: ignore[arg-type]
        ),
    )
    app.state.verifier = _verifier()
    client = TestClient(app)
    plain = {"Authorization": f"Bearer {_token()}"}
    assert (
        client.post("/v1/ingestions", json={"url": "https://x"}, headers=plain).status_code == 403
    )
    assert client.post("/v1/ingestions", json={"url": "https://x"}).status_code == 401
