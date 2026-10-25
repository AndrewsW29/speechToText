"""Resumable upload through the real tusd server: drop at 60%, resume, and exactly one document appears."""

import base64
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

from tests.pdf_fixtures import build_pdf

ROOT = Path(__file__).resolve().parents[3]
TUS = {"Tus-Resumable": "1.0.0"}
pytestmark = pytest.mark.integration


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait(url: str, timeout: float = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(url, timeout=1).status_code < 500:
                return
        except httpx.HTTPError:
            time.sleep(0.5)
    pytest.fail(f"{url} did not come up")


@pytest.fixture
def stack() -> Iterator[tuple[str, str]]:
    if (
        subprocess.run(
            ["docker", "image", "inspect", "tusproject/tusd:v2"], capture_output=True
        ).returncode
        != 0
    ):
        pytest.skip("docker image tusproject/tusd:v2 not available")
    # Docker Desktop/colima only share the home directory with containers, so not the system temp dir.
    work = Path(tempfile.mkdtemp(prefix=".tus-", dir=ROOT))
    api_port, tus_port, token = _free_port(), _free_port(), uuid.uuid4().hex
    uploads, data = work / "uploads", work / "data"
    uploads.mkdir()
    uploads.chmod(0o777)  # tusd runs as its own non-root user inside the container
    env = {
        **os.environ,
        "VA_ENVIRONMENT": "local",
        "VA_AUTH_ENABLED": "false",
        "VA_STT_ENGINE": "fake",
        "VA_PDF_ENABLED": "true",
        "VA_PDF_STORAGE_DIR": str(data),
        "VA_TUS_HOOK_TOKEN": token,
        "VA_TUS_UPLOAD_DIR": str(uploads),
        "VA_PDF_INGEST__SECURITY__SCAN_MALWARE": "false",
    }
    api = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:create_app",
            "--factory",
            "--host",
            "0.0.0.0",
            "--port",
            str(api_port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    name = f"tusd-test-{uuid.uuid4().hex[:8]}"
    try:
        _wait(f"http://127.0.0.1:{api_port}/health/live")
        subprocess.run(  # noqa: S603
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "--name",
                name,
                "--add-host",
                "host.docker.internal:host-gateway",
                "-v",
                f"{uploads}:/data",
                "-p",
                f"{tus_port}:8080",
                "tusproject/tusd:v2",
                "-upload-dir",
                "/data",
                "-hooks-enabled-events",
                "pre-create,post-finish",
                "-hooks-http",
                f"http://host.docker.internal:{api_port}/internal/tus/hooks/{token}",
            ],
            check=True,
            capture_output=True,
        )
        _wait(f"http://127.0.0.1:{tus_port}/files/")
        yield f"http://127.0.0.1:{api_port}", f"http://127.0.0.1:{tus_port}"
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)  # noqa: S603
        api.terminate()
        api.wait(timeout=10)
        shutil.rmtree(work, ignore_errors=True)


def _documents(api: str) -> list[dict]:
    return httpx.get(f"{api}/v1/documents", timeout=5).json()["items"]


def test_an_upload_dropped_at_60_percent_resumes_and_creates_one_document(stack) -> None:  # type: ignore[no-untyped-def]
    api, tus = stack
    data = build_pdf(40) + b"\n%" + b"x" * 200_000 + b"\n"  # comment padding keeps it a valid PDF
    cut = int(len(data) * 0.6)
    filename = base64.b64encode(b"big-guide.pdf").decode()

    created = httpx.post(
        f"{tus}/files/",
        headers={**TUS, "Upload-Length": str(len(data)), "Upload-Metadata": f"filename {filename}"},
        timeout=10,
    )
    assert created.status_code == 201
    location = created.headers["Location"]
    url = location if location.startswith("http") else f"{tus}{location}"
    url = url.replace("localhost", "127.0.0.1")
    if "host.docker.internal" in url:
        url = f"{tus}{httpx.URL(url).path}"

    first = httpx.patch(
        url,
        content=data[:cut],
        headers={**TUS, "Upload-Offset": "0", "Content-Type": "application/offset+octet-stream"},
        timeout=30,
    )
    assert first.status_code == 204 and int(first.headers["Upload-Offset"]) == cut
    assert _documents(api) == []  # nothing is ingested before the upload finishes

    # the connection "dropped": a new client asks where to continue
    offset = int(httpx.head(url, headers=TUS, timeout=10).headers["Upload-Offset"])
    assert offset == cut
    done = httpx.patch(
        url,
        content=data[offset:],
        headers={
            **TUS,
            "Upload-Offset": str(offset),
            "Content-Type": "application/offset+octet-stream",
        },
        timeout=30,
    )
    assert done.status_code == 204 and int(done.headers["Upload-Offset"]) == len(data)

    deadline = time.time() + 30
    while time.time() < deadline:
        items = _documents(api)
        if items and items[0]["status"] in {"failed", "ready", "quarantined"}:
            break
        time.sleep(0.3)
    items = _documents(api)
    assert len(items) == 1 and items[0]["title"] == "big-guide.pdf"
    assert items[0]["status"] in {"failed", "ready"}  # no reader yet: ends reader_not_configured
    assert items[0]["failure_reason"] in {None, "reader_not_configured"}
