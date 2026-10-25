"""ClamAV (clamd) scanner over the INSTREAM protocol. Any doubt fails closed."""

from __future__ import annotations

import socket
import struct

from app.application.errors import ScannerUnavailableError
from app.application.pdf.ports.malware_scanner import MalwareScanner, ScanResult

CHUNK = 64 * 1024


class ClamAvScanner(MalwareScanner):
    def __init__(self, host: str, port: int = 3310, timeout: float = 30.0) -> None:
        self._address = (host, port)
        self._timeout = timeout

    def scan(self, data: bytes) -> ScanResult:
        try:
            with socket.create_connection(self._address, timeout=self._timeout) as conn:
                conn.sendall(b"zINSTREAM\0")
                for start in range(0, len(data), CHUNK):
                    chunk = data[start : start + CHUNK]
                    conn.sendall(struct.pack("!I", len(chunk)) + chunk)
                conn.sendall(struct.pack("!I", 0))
                reply = self._read_reply(conn)
        except OSError as exc:
            raise ScannerUnavailableError("malware scanner unreachable") from exc
        return self._parse(reply)

    @staticmethod
    def _read_reply(conn: socket.socket) -> str:
        buffer = b""
        while not buffer.endswith(b"\0") and (chunk := conn.recv(4096)):
            buffer += chunk
        return buffer.rstrip(b"\0").decode("utf-8", "replace").strip()

    @staticmethod
    def _parse(reply: str) -> ScanResult:
        if reply.endswith("OK"):
            return ScanResult(clean=True)
        if reply.endswith("FOUND"):
            signature = reply.removeprefix("stream:").removesuffix("FOUND").strip()
            return ScanResult(clean=False, signature=signature or "unknown")
        raise ScannerUnavailableError(f"unexpected scanner reply: {reply[:80]!r}")
