"""Run the committed collection with Newman against a live API (fake STT, auth disabled)."""

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
POSTMAN = ROOT / "postman"
pytestmark = pytest.mark.integration


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _newman_command(port: int) -> list[str]:
    args = [
        "run",
        "voice-assistant.postman_collection.json",
        "-e",
        "environments/local.postman_environment.json",
        "--env-var",
        f"baseUrl=http://HOST:{port}",
        "--env-var",
        "authEnabled=false",
        "--env-var",
        "smallAudioLimit=true",
        "--bail",
        "--reporters",
        "cli",
    ]
    if shutil.which("newman"):
        return [
            "newman",
            *[a.replace("HOST", "localhost") for a in args],
            "--working-dir",
            str(POSTMAN),
        ]
    if shutil.which("docker"):
        probe = subprocess.run(
            ["docker", "image", "inspect", "postman/newman:alpine"], capture_output=True
        )
        if probe.returncode == 0:
            return [
                "docker",
                "run",
                "--rm",
                "--add-host",
                "host.docker.internal:host-gateway",
                "-v",
                f"{POSTMAN}:/etc/newman",
                "-w",
                "/etc/newman",
                "postman/newman:alpine",
                *[a.replace("HOST", "host.docker.internal") for a in args],
            ]
    pytest.skip("newman is not installed (npm i -g newman, or docker pull postman/newman:alpine)")
    return []


@pytest.fixture
def live_api() -> tuple[int, subprocess.Popen[bytes]]:
    port = _free_port()
    env = {
        **os.environ,
        "VA_AUTH_ENABLED": "false",
        "VA_STT_ENGINE": "fake",
        "VA_MAX_AUDIO_BYTES": "2048",
    }
    proc = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:create_app",
            "--factory",
            "--port",
            str(port),
            "--host",
            "0.0.0.0",
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(60):
            try:
                if httpx.get(f"http://127.0.0.1:{port}/health/live", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.5)
        else:
            pytest.fail("API did not start")
        yield port, proc
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def test_collection_passes_against_the_live_api(live_api) -> None:  # type: ignore[no-untyped-def]
    port, _ = live_api
    result = subprocess.run(_newman_command(port), capture_output=True, text=True, timeout=300)  # noqa: S603
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-1000:]
