"""MinIO/S3 original storage: content-addressed by SHA-256 and never overwritten."""

from __future__ import annotations

import hashlib
import io
from typing import Any

from minio.error import S3Error

from app.application.errors import StorageError
from app.application.pdf.ports.object_store import ObjectStore


def key_for(sha256: str) -> str:
    return f"sha256/{sha256[:2]}/{sha256}"


class MinioObjectStore(ObjectStore):
    def __init__(self, client: Any, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def put(self, data: bytes) -> str:
        key = key_for(hashlib.sha256(data).hexdigest())
        try:
            if self._exists(key):
                return key  # originals are immutable: never overwrite
            self._client.put_object(
                self._bucket, key, io.BytesIO(data), len(data), content_type="application/pdf"
            )
        except (OSError, S3Error) as exc:
            raise StorageError("could not store the original file") from exc
        return key

    def get(self, key: str) -> bytes:
        try:
            response = self._client.get_object(self._bucket, key)
        except S3Error as exc:
            raise StorageError(f"missing object {key}") from exc
        except OSError as exc:
            raise StorageError("object store unreachable") from exc
        try:
            return bytes(response.read())
        finally:
            response.close()
            response.release_conn()

    def exists(self, key: str) -> bool:
        try:
            return self._exists(key)
        except OSError as exc:
            raise StorageError("object store unreachable") from exc

    def delete(self, key: str) -> None:
        try:
            self._client.remove_object(self._bucket, key)
        except S3Error:
            return
        except OSError as exc:
            raise StorageError("object store unreachable") from exc

    def _exists(self, key: str) -> bool:
        try:
            self._client.stat_object(self._bucket, key)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject", "NotFound"}:
                return False
            raise
        return True
