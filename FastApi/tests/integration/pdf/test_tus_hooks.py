from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.integration.pdf.test_documents_api import Rig
from tests.pdf_fixtures import build_pdf, zip_renamed_as_pdf

TOKEN = "s3cret-hook-token"


@pytest.fixture
def rig(tmp_path: Path) -> Rig:
    return Rig(tus_hook_token=TOKEN, tus_upload_dir=tmp_path)


def _event(kind: str, upload_id: str = "abc123", size: int = 100, **headers: str) -> dict:
    return {
        "Type": kind,
        "Event": {
            "Upload": {"ID": upload_id, "Size": size, "MetaData": {"filename": "guide.pdf"}},
            "HTTPRequest": {"Method": "PATCH", "Header": {k: [v] for k, v in headers.items()}},
        },
    }


def _post(client: TestClient, payload: dict, token: str = TOKEN):  # type: ignore[no-untyped-def]
    return client.post(f"/internal/tus/hooks/{token}", json=payload)


def test_the_hook_url_requires_the_secret_token(rig: Rig) -> None:
    assert _post(rig.client, _event("post-finish"), token="wrong").status_code == 404


def test_hook_endpoints_are_not_part_of_the_public_api(rig: Rig) -> None:
    assert not any("/internal" in p for p in rig.client.get("/openapi.json").json()["paths"])


def test_post_finish_ingests_the_finished_upload_and_removes_the_temporary_files(
    rig: Rig, tmp_path: Path
) -> None:
    (tmp_path / "abc123").write_bytes(build_pdf(2))
    (tmp_path / "abc123.info").write_text("{}")
    response = _post(rig.client, _event("post-finish"))
    assert response.status_code == 200 and response.json()["document_id"].startswith("d_")
    assert [d.title for d in rig.repo.all()] == ["guide.pdf"] and rig.repo.all()[
        0
    ].status.value == "ready"
    assert not (tmp_path / "abc123").exists() and not (tmp_path / "abc123.info").exists()


def test_a_finished_upload_that_is_not_a_pdf_creates_nothing(rig: Rig, tmp_path: Path) -> None:
    (tmp_path / "abc123").write_bytes(zip_renamed_as_pdf())
    response = _post(rig.client, _event("post-finish"))
    assert response.status_code == 200 and response.json() == {"rejected": "not_a_pdf"}
    assert rig.repo.all() == [] and not (tmp_path / "abc123").exists()


@pytest.mark.parametrize("bad_id", ["../../etc/passwd", "a/b", "abc.def", ""])
def test_upload_ids_cannot_escape_the_upload_directory(rig: Rig, bad_id: str) -> None:
    assert _post(rig.client, _event("post-finish", upload_id=bad_id)).status_code in {400, 422}


def test_pre_create_rejects_oversized_uploads_before_a_byte_is_sent(tmp_path: Path) -> None:
    rig = Rig(
        tus_hook_token=TOKEN, tus_upload_dir=tmp_path, pdf_ingest={"limits": {"max_file_mb": 1}}
    )
    body = _post(rig.client, _event("pre-create", size=5 * 1024 * 1024)).json()
    assert body["RejectUpload"] is True and body["HTTPResponse"]["StatusCode"] == 413
    assert _post(rig.client, _event("pre-create", size=1000)).json() == {}


def test_with_auth_enabled_hooks_need_a_valid_bearer_token(tmp_path: Path) -> None:
    rig = Rig(auth=True, tus_hook_token=TOKEN, tus_upload_dir=tmp_path)
    rejected = _post(rig.client, _event("pre-create")).json()
    assert rejected["RejectUpload"] is True and rejected["HTTPResponse"]["StatusCode"] == 401
    ok = _post(
        rig.client, _event("pre-create", Authorization=rig.headers("alice")["Authorization"])
    ).json()
    assert ok == {}
    (tmp_path / "abc123").write_bytes(build_pdf())
    done = _post(
        rig.client, _event("post-finish", Authorization=rig.headers("alice")["Authorization"])
    )
    assert done.status_code == 200 and rig.repo.all()[0].owner == "alice"


def test_post_finish_without_credentials_when_auth_is_on_drops_the_file(tmp_path: Path) -> None:
    rig = Rig(auth=True, tus_hook_token=TOKEN, tus_upload_dir=tmp_path)
    (tmp_path / "abc123").write_bytes(build_pdf())
    assert _post(rig.client, _event("post-finish")).json() == {"rejected": "unauthorized"}
    assert rig.repo.all() == [] and not (tmp_path / "abc123").exists()


def test_other_events_are_acknowledged_and_ignored(rig: Rig) -> None:
    assert _post(rig.client, _event("post-receive")).json() == {}
