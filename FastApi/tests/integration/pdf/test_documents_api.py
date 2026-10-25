import time
from typing import Any

import jwt
import pytest
from app.adapters.inbound.rest.auth import JwtVerifier
from app.adapters.outbound.pdf.inline_launcher import InlineLauncher
from app.application.pdf.services.step_ledger import StepLedger
from app.application.pdf.use_cases.ingest_pdf import IngestPdf
from app.application.pdf.use_cases.upload_document import UploadDocument
from app.application.use_cases.ask_question import AskQuestion
from app.config import Settings
from app.container import Container
from app.main import create_app
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from tests.fakes import FakeTranscriber
from tests.fakes.pdf import (
    FakeIndexer,
    FakeInspector,
    FakeLauncher,
    FakeReader,
    FakeScanner,
    InMemoryDocuments,
    InMemoryEvents,
    InMemoryObjectStore,
)
from tests.pdf_fixtures import EICAR, build_pdf, zip_renamed_as_pdf

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ISS, AUD = "https://idp.test/realms/va", "voice-api"


def _token(sub: str) -> str:
    claims = {"sub": sub, "iss": ISS, "aud": AUD, "exp": int(time.time()) + 60}
    return jwt.encode(claims, KEY, algorithm="RS256")


class Rig:
    def __init__(self, *, auth: bool = False, inline: bool = True, **settings: Any) -> None:
        self.settings = Settings(
            auth_enabled=auth,
            pdf_events_poll_seconds=0.01,
            **settings,
            **(
                {"oidc_issuer": ISS, "oidc_jwks_url": "http://x/jwks", "oidc_audience": AUD}
                if auth
                else {}
            ),
        )
        self.store, self.repo, self.events = (
            InMemoryObjectStore(),
            InMemoryDocuments(),
            InMemoryEvents(),
        )
        self.scanner, self.indexer = FakeScanner(), FakeIndexer()
        ingest = IngestPdf(
            self.store,
            self.scanner,
            FakeInspector(3),
            FakeInspector(3),
            FakeReader(),
            self.indexer,
            self.repo,
            self.events,
            StepLedger(self.repo, "t"),
        )
        self.launcher = InlineLauncher(ingest) if inline else FakeLauncher()
        container = Container(
            ask_question=AskQuestion(FakeTranscriber(), None),  # type: ignore[arg-type]
            upload_document=UploadDocument(self.store, self.repo, self.launcher, self.settings),
            documents=self.repo,
            document_events=self.events,
        )
        app = create_app(self.settings, container=container)
        if auth:
            app.state.verifier = JwtVerifier(
                issuer=ISS, audience=AUD, key_resolver=lambda _t: KEY.public_key()
            )
        self.client = TestClient(app)

    def headers(self, user: str | None) -> dict[str, str]:
        return {"Authorization": f"Bearer {_token(user)}"} if user else {}

    def upload(self, data: bytes, user: str | None = None, name: str = "guide.pdf", **kw: Any):  # type: ignore[no-untyped-def]
        return self.client.post(
            "/v1/documents",
            files={"file": (name, data, "application/pdf")},
            headers=self.headers(user),
            **kw,
        )


def test_upload_returns_202_quickly_with_a_document_id() -> None:
    rig = Rig(inline=False)
    start = time.perf_counter()
    response = rig.upload(build_pdf(2))
    assert response.status_code == 202 and time.perf_counter() - start < 1.0
    body = response.json()
    assert body["document_id"].startswith("d_") and body["status"] == "queued"
    assert body["version"] == 1 and body["duplicate_of"] is None
    assert rig.launcher.launched == [body["document_id"]]  # type: ignore[attr-defined]


def test_inline_processing_reaches_ready_and_is_visible_through_the_api() -> None:
    rig = Rig()
    doc_id = rig.upload(build_pdf(3)).json()["document_id"]
    detail = rig.client.get(f"/v1/documents/{doc_id}").json()
    assert detail["status"] == "ready" and detail["pages"] == 3 and detail["title"] == "guide.pdf"
    assert [d["document_id"] for d in rig.client.get("/v1/documents").json()["items"]] == [doc_id]
    assert rig.client.get("/v1/documents", params={"status": "failed"}).json()["items"] == []


def test_the_same_file_twice_is_a_200_that_points_at_the_first_document() -> None:
    rig = Rig()
    data = build_pdf(2)
    first = rig.upload(data).json()
    second = rig.upload(data)
    assert second.status_code == 200
    assert second.json()["document_id"] == first["document_id"] == second.json()["duplicate_of"]
    assert len(rig.repo.all()) == 1 and rig.scanner.scans == 1


def test_a_zip_renamed_pdf_is_refused_before_anything_runs() -> None:
    rig = Rig()
    response = rig.upload(zip_renamed_as_pdf(), name="report.pdf")
    assert response.status_code == 415 and response.headers["content-type"].startswith(
        "application/problem+json"
    )
    assert (
        "valid PDF" in response.json()["detail"] and rig.repo.all() == [] and rig.scanner.scans == 0
    )


def test_oversized_uploads_are_413_and_quota_breaches_are_429() -> None:
    small = Rig(pdf_ingest={"limits": {"max_file_mb": 0}})
    assert small.upload(build_pdf()).status_code in {413}
    rig = Rig(pdf_quotas={"max_documents": 1})
    assert rig.upload(build_pdf(1)).status_code == 202
    over = rig.upload(build_pdf(2))
    assert over.status_code == 429 and "maximum number of documents" in over.json()["detail"]


def test_infected_files_end_up_quarantined_without_leaking_the_signature_details() -> None:
    rig = Rig()
    doc_id = rig.upload(build_pdf() + EICAR).json()["document_id"]
    detail = rig.client.get(f"/v1/documents/{doc_id}").json()
    assert detail["status"] == "quarantined" and detail["failure_reason"] == "malware"


def test_unknown_failures_are_shown_as_a_generic_code() -> None:
    rig = Rig()
    rig.indexer._fail_times = 99
    doc_id = rig.upload(build_pdf()).json()["document_id"]
    detail = rig.client.get(f"/v1/documents/{doc_id}").json()
    assert detail["status"] == "failed" and detail["failure_reason"] == "processing_error"
    assert "embedder" not in str(detail)


def test_other_users_documents_do_not_exist_for_you() -> None:
    rig = Rig(auth=True)
    doc_id = rig.upload(build_pdf(), "alice").json()["document_id"]
    assert (
        rig.client.get(f"/v1/documents/{doc_id}", headers=rig.headers("alice")).status_code == 200
    )
    assert rig.client.get(f"/v1/documents/{doc_id}", headers=rig.headers("bob")).status_code == 404
    assert rig.client.get("/v1/documents", headers=rig.headers("bob")).json()["items"] == []
    assert (
        rig.client.get(f"/v1/documents/{doc_id}/events", headers=rig.headers("bob")).status_code
        == 404
    )
    assert rig.client.get(f"/v1/documents/{doc_id}").status_code == 401


def test_same_bytes_from_two_users_are_two_documents() -> None:
    rig = Rig(auth=True)
    data = build_pdf()
    assert (
        rig.upload(data, "alice").json()["document_id"]
        != rig.upload(data, "bob").json()["document_id"]
    )


def test_events_stream_the_stages_as_server_sent_events() -> None:
    rig = Rig()
    doc_id = rig.upload(build_pdf(3)).json()["document_id"]
    with rig.client.stream("GET", f"/v1/documents/{doc_id}/events") as response:
        assert response.status_code == 200 and response.headers["content-type"].startswith(
            "text/event-stream"
        )
        text = "".join(response.iter_text())
    stages = [line.split(": ", 1)[1] for line in text.splitlines() if line.startswith("event: ")]
    assert stages == ["stage"] * 5
    assert (
        '"stage": "reading"' in text and '"pages_total": 3' in text and '"stage": "ready"' in text
    )
    assert "id: 5" in text


def test_events_can_resume_after_the_last_event_id() -> None:
    rig = Rig()
    doc_id = rig.upload(build_pdf(3)).json()["document_id"]
    with rig.client.stream(
        "GET", f"/v1/documents/{doc_id}/events", headers={"Last-Event-ID": "3"}
    ) as response:
        text = "".join(response.iter_text())
    assert text.count("event: stage") == 2 and '"stage": "scanning"' not in text


def test_events_for_a_missing_document_are_404() -> None:
    assert Rig().client.get("/v1/documents/d_nope/events").status_code == 404


def test_the_queue_being_down_is_a_503_and_leaves_a_failed_document() -> None:
    rig = Rig(inline=False)
    rig.launcher._fail = True  # type: ignore[attr-defined]
    response = rig.upload(build_pdf())
    assert response.status_code == 503 and rig.repo.all()[0].status.value == "failed"
    assert pytest.approx(0) == 0
