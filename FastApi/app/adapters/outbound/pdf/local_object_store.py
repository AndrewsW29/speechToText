"""Filesystem original storage for local development and tests. Same contract as the MinIO store."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

from app.application.errors import StorageError
from app.application.pdf.ports.object_store import ObjectStore


class LocalFileObjectStore(ObjectStore):
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if self._root not in path.parents:
            raise StorageError("invalid object key")
        return path

    def put(self, data: bytes) -> str:
        digest = hashlib.sha256(data).hexdigest()
        key = f"sha256/{digest[:2]}/{digest}"
        path = self._path(key)
        if path.exists():
            return key  # immutable
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
            os.replace(tmp, path)  # atomic: readers never see a partial file
        except OSError as exc:
            Path(tmp).unlink(missing_ok=True)
            raise StorageError("could not store the original file") from exc
        return key

    def get(self, key: str) -> bytes:
        try:
            return self._path(key).read_bytes()
        except OSError as exc:
            raise StorageError(f"missing object {key}") from exc

    def exists(self, key: str) -> bool:
        try:
            return self._path(key).is_file()
        except StorageError:
            return False

    def delete(self, key: str) -> None:
        try:
            self._path(key).unlink(missing_ok=True)
        except OSError as exc:
            raise StorageError("could not delete the object") from exc
