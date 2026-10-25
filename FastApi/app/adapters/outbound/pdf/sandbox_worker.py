"""Runs inside the sandbox subprocess (`python -m ...sandbox_worker <function>`).

Reads the payload from stdin, writes the result to stdout. It never trusts the PDF: the runner
limits CPU, memory, file size and wall clock; this module denies network access as defence in depth.
"""

from __future__ import annotations

import io
import json
import os
import signal
import sys
import tempfile
from collections.abc import Callable

import pikepdf

from app.adapters.outbound.pdf.active_content import _scan, strip_active_content


def deny_network() -> None:
    import socket

    class DeniedSocket(socket.socket):
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise PermissionError("network access denied in the PDF sandbox")

    def denied(*_args: object, **_kwargs: object) -> None:
        raise PermissionError("network access denied in the PDF sandbox")

    socket.socket = DeniedSocket  # type: ignore[misc]
    socket.create_connection = denied  # type: ignore[assignment]
    socket.getaddrinfo = denied  # type: ignore[assignment]


def inspect(payload: bytes) -> bytes:
    try:
        with pikepdf.open(io.BytesIO(payload)) as pdf:
            result = {
                "page_count": len(pdf.pages),
                "encrypted": False,
                "active_content": sorted(_scan(pdf)),
            }
    except pikepdf.PasswordError:
        result = {"page_count": 0, "encrypted": True, "active_content": []}
    except pikepdf.PdfError:
        result = {"error": "not_a_pdf"}
    return json.dumps(result).encode()


def strip(payload: bytes) -> bytes:
    return strip_active_content(payload)


# ---- diagnostics: only reachable when the runner enables them (tests), never in production ----
def spin(_: bytes) -> bytes:
    while True:
        pass


def whoami(_: bytes) -> bytes:
    return json.dumps({"pid": os.getpid(), "cwd": os.getcwd(), "env": sorted(os.environ)}).encode()


def connect(payload: bytes) -> bytes:
    import socket

    try:
        socket.create_connection(("127.0.0.1", int(payload)), timeout=1)
        return json.dumps({"connected": True, "error": ""}).encode()
    except OSError as exc:
        return json.dumps({"connected": False, "error": str(exc)}).encode()


def write_big(_: bytes) -> bytes:
    try:
        with tempfile.NamedTemporaryFile(dir=os.getcwd()) as handle:
            handle.write(b"x" * 1_000_000)
            handle.flush()
        return json.dumps({"wrote": True}).encode()
    except OSError:
        return json.dumps({"wrote": False}).encode()


def alloc(_: bytes) -> bytes:
    hog = []
    while True:
        hog.append(bytearray(32 * 1024 * 1024))


FUNCTIONS: dict[str, Callable[[bytes], bytes]] = {"inspect": inspect, "strip": strip}
DIAGNOSTICS: dict[str, Callable[[bytes], bytes]] = {
    "spin": spin,
    "whoami": whoami,
    "connect": connect,
    "write_big": write_big,
    "alloc": alloc,
}


def main(argv: list[str]) -> int:
    signal.signal(
        signal.SIGXFSZ, signal.SIG_IGN
    )  # let oversized writes fail with OSError instead of dying
    deny_network()
    functions = dict(FUNCTIONS)
    if os.environ.get("SANDBOX_DIAGNOSTICS") == "1":
        functions.update(DIAGNOSTICS)
    function = functions.get(argv[1]) if len(argv) > 1 else None
    if function is None:
        sys.stderr.write("unknown sandbox function\n")
        return 2
    sys.stdout.buffer.write(function(sys.stdin.buffer.read()))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
