"""Sandbox for untrusted PDF parsing: one document per process, hard resource limits, scrubbed
environment, throwaway working directory, no network (denied in the worker; also enforce it at the
container/pod level with `--network none` / a deny-all NetworkPolicy)."""

from __future__ import annotations

import json
import os
import resource
import signal
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.application.errors import ApplicationError, NotAPdfError, PixelBudgetExceededError
from app.application.pdf.ports.pdf_inspector import ActiveContentStripper, Inspection, PdfInspector

APP_ROOT = Path(__file__).resolve().parents[4]
WORKER = "app.adapters.outbound.pdf.sandbox_worker"


class SandboxTimeoutError(ApplicationError):
    """The job exceeded its wall-clock or CPU budget and was killed."""


class SandboxCrashedError(ApplicationError):
    """The worker died, was killed by a resource limit, or produced no usable output."""


@dataclass(frozen=True, slots=True)
class SandboxLimits:
    cpu_seconds: int = 60
    wall_seconds: int = 120
    memory_bytes: int = 2 * 1024 * 1024 * 1024
    max_file_bytes: int = 64 * 1024 * 1024
    max_open_files: int = 64
    max_output_bytes: int = 64 * 1024 * 1024
    max_pixels: int = 50_000_000


def assert_within_pixel_budget(width: int, height: int, max_pixels: int) -> None:
    """Call before rendering: a tiny file can claim an enormous canvas (decompression bomb)."""
    if width * height > max_pixels:
        raise PixelBudgetExceededError(
            f"page would need {width * height:,} pixels (limit {max_pixels:,})"
        )


def _apply_limits(limits: SandboxLimits) -> Callable[[], None]:
    def preexec() -> None:
        resource.setrlimit(resource.RLIMIT_CPU, (limits.cpu_seconds, limits.cpu_seconds + 1))
        resource.setrlimit(resource.RLIMIT_FSIZE, (limits.max_file_bytes, limits.max_file_bytes))
        resource.setrlimit(resource.RLIMIT_NOFILE, (limits.max_open_files, limits.max_open_files))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        if sys.platform == "linux":  # not enforced on macOS
            resource.setrlimit(resource.RLIMIT_AS, (limits.memory_bytes, limits.memory_bytes))

    return preexec


class SandboxRunner:
    def __init__(self, diagnostics: bool = False, python: str = sys.executable) -> None:
        self._diagnostics = diagnostics
        self._python = python

    def run(self, function: str, payload: bytes, limits: SandboxLimits | None = None) -> bytes:
        limits = limits or SandboxLimits()
        env = {
            "PYTHONPATH": str(APP_ROOT),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "LANG": "C.UTF-8",
            "SANDBOX_MAX_PIXELS": str(limits.max_pixels),
        }
        if self._diagnostics:
            env["SANDBOX_DIAGNOSTICS"] = "1"
        with tempfile.TemporaryDirectory(prefix="pdf-sandbox-") as workdir:
            proc = subprocess.Popen(  # noqa: S603
                [self._python, "-s", "-m", WORKER, function],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=workdir,
                env=env,
                preexec_fn=_apply_limits(limits),
                start_new_session=True,
            )
            try:
                out, _ = proc.communicate(payload, timeout=limits.wall_seconds)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
                raise SandboxTimeoutError(f"{function} exceeded {limits.wall_seconds}s") from None
        if proc.returncode != 0:
            signalled = -proc.returncode if proc.returncode < 0 else None
            if signalled in {signal.SIGXCPU, signal.SIGKILL}:
                raise SandboxTimeoutError(f"{function} exceeded its CPU budget")
            raise SandboxCrashedError(f"{function} failed (exit {proc.returncode})")
        if len(out) > limits.max_output_bytes:
            raise SandboxCrashedError("sandbox output too large")
        return out


class SandboxedPdfInspector(PdfInspector, ActiveContentStripper):
    """Inspection and stripping happen in the sandbox; the API process never parses the PDF."""

    def __init__(self, runner: SandboxRunner, limits: SandboxLimits | None = None) -> None:
        self._runner = runner
        self._limits = limits or SandboxLimits()

    def inspect(self, data: bytes) -> Inspection:
        result = json.loads(self._runner.run("inspect", data, self._limits))
        if result.get("error") == "not_a_pdf":
            raise NotAPdfError
        return Inspection(
            page_count=int(result["page_count"]),
            encrypted=bool(result["encrypted"]),
            active_content=frozenset(result["active_content"]),
        )

    def strip(self, data: bytes) -> bytes:
        return self._runner.run("strip", data, self._limits)
