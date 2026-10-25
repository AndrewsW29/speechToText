import json
import os
import socket
import sys

import pytest
from app.adapters.outbound.pdf.sandbox import (
    SandboxCrashedError,
    SandboxedPdfInspector,
    SandboxLimits,
    SandboxRunner,
    SandboxTimeoutError,
    assert_within_pixel_budget,
)
from app.application.errors import NotAPdfError, PixelBudgetExceededError

from tests.pdf_fixtures import build_pdf

FAST = SandboxLimits(cpu_seconds=2, wall_seconds=3, memory_bytes=512 * 1024 * 1024)


def _run(function: str, payload: bytes = b"", limits: SandboxLimits = FAST) -> dict:
    return json.loads(SandboxRunner(diagnostics=True).run(function, payload, limits))


def test_a_runaway_job_is_killed_by_the_wall_clock() -> None:
    with pytest.raises(SandboxTimeoutError):
        SandboxRunner(diagnostics=True).run(
            "spin", b"", SandboxLimits(cpu_seconds=60, wall_seconds=1)
        )


def test_cpu_limit_kills_a_busy_loop_even_with_a_generous_wall_clock() -> None:
    with pytest.raises((SandboxTimeoutError, SandboxCrashedError)):
        SandboxRunner(diagnostics=True).run(
            "spin", b"", SandboxLimits(cpu_seconds=1, wall_seconds=20)
        )


def test_every_run_is_a_fresh_process_in_a_throwaway_directory() -> None:
    a, b = _run("whoami"), _run("whoami")
    assert a["pid"] != b["pid"] != os.getpid()
    assert a["cwd"] != b["cwd"] and not os.path.exists(a["cwd"])
    assert os.listdir(a["cwd"]) if os.path.exists(a["cwd"]) else True


def test_the_environment_is_scrubbed_of_secrets() -> None:
    os.environ["VA_DATABASE_URL"] = "postgresql://user:hunter2@db/x"
    try:
        report = _run("whoami")
    finally:
        del os.environ["VA_DATABASE_URL"]
    assert not [k for k in report["env"] if k.startswith(("VA_", "AWS_", "MINIO"))]
    assert "hunter2" not in json.dumps(report)


def test_network_access_is_denied_inside_the_worker() -> None:
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    try:
        report = _run("connect", str(server.getsockname()[1]).encode())
    finally:
        server.close()
    assert report["connected"] is False and "denied" in report["error"].lower()


def test_writing_large_files_is_blocked_by_the_file_size_limit() -> None:
    report = _run(
        "write_big", b"", SandboxLimits(cpu_seconds=2, wall_seconds=3, max_file_bytes=1024)
    )
    assert report["wrote"] is False


@pytest.mark.skipif(sys.platform != "linux", reason="RLIMIT_AS is not enforced on macOS")
def test_memory_hogs_are_killed() -> None:
    with pytest.raises((SandboxCrashedError, SandboxTimeoutError)):
        SandboxRunner(diagnostics=True).run(
            "alloc",
            b"",
            SandboxLimits(cpu_seconds=5, wall_seconds=5, memory_bytes=64 * 1024 * 1024),
        )


def test_diagnostics_are_unavailable_unless_explicitly_enabled() -> None:
    with pytest.raises(SandboxCrashedError):
        SandboxRunner().run("spin", b"", FAST)


def test_pixel_budget_rejects_decompression_bomb_sized_renders() -> None:
    assert_within_pixel_budget(2480, 3508, max_pixels=50_000_000)  # A4 at 300 DPI
    with pytest.raises(PixelBudgetExceededError):
        assert_within_pixel_budget(30_000, 30_000, max_pixels=50_000_000)


def test_inspector_runs_in_the_sandbox_and_reports_pages_and_active_content() -> None:
    inspection = SandboxedPdfInspector(SandboxRunner()).inspect(build_pdf(4, javascript=True))
    assert inspection.page_count == 4 and inspection.active_content == frozenset({"javascript"})
    assert not inspection.encrypted


def test_inspector_flags_encryption_and_rejects_non_pdf_input() -> None:
    inspector = SandboxedPdfInspector(SandboxRunner())
    assert inspector.inspect(build_pdf(2, password="secret")).encrypted
    with pytest.raises(NotAPdfError):
        inspector.inspect(b"%PDF-1.4 this is not a real pdf structure at all")
