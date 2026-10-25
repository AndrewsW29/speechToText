"""A tiny clamd look-alike speaking the INSTREAM protocol, so the adapter is tested over real sockets."""

from __future__ import annotations

import socketserver
import struct
import threading

from tests.pdf_fixtures import EICAR


class _Handler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        command = b""
        while not command.endswith(b"\0"):
            command += self.request.recv(1)
        if command != b"zINSTREAM\0":
            self.request.sendall(b"UNKNOWN COMMAND\0")
            return
        received = b""
        while True:
            header = self._read(4)
            (size,) = struct.unpack("!I", header)
            if size == 0:
                break
            received += self._read(size)
            if len(received) > self.server.limit:  # type: ignore[attr-defined]
                self.request.sendall(b"INSTREAM size limit exceeded. ERROR\0")
                return
        if EICAR in received:
            self.request.sendall(b"stream: Eicar-Test-Signature FOUND\0")
        else:
            self.request.sendall(b"stream: OK\0")

    def _read(self, n: int) -> bytes:
        data = b""
        while len(data) < n:
            chunk = self.request.recv(n - len(data))
            if not chunk:
                raise ConnectionError("client went away")
            data += chunk
        return data


class FakeClamd:
    def __init__(self, limit: int = 10_000_000) -> None:
        self._server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), _Handler)
        self._server.limit = limit  # type: ignore[attr-defined]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    def __enter__(self) -> FakeClamd:
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()
