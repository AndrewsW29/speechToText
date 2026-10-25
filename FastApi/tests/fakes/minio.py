from __future__ import annotations

import io

from minio.error import S3Error


def _not_found(key: str) -> S3Error:
    return S3Error(None, "NoSuchKey", "not found", key, "req", "host")  # type: ignore[arg-type]


class _Response:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data

    def close(self) -> None: ...

    def release_conn(self) -> None: ...


class FakeMinio:
    """Just enough of the MinIO client: put_object, get_object, stat_object, remove_object."""

    def __init__(self, fail: bool = False) -> None:
        self.objects: dict[str, bytes] = {}
        self.put_calls = 0
        self.last_length = 0
        self._fail = fail

    def _check(self) -> None:
        if self._fail:
            raise ConnectionError("minio unreachable")

    def put_object(self, bucket: str, key: str, data: io.BytesIO, length: int, **_: object) -> None:
        self._check()
        self.put_calls += 1
        self.last_length = length
        self.objects[key] = data.read()

    def get_object(self, bucket: str, key: str) -> _Response:
        self._check()
        if key not in self.objects:
            raise _not_found(key)
        return _Response(self.objects[key])

    def stat_object(self, bucket: str, key: str) -> object:
        self._check()
        if key not in self.objects:
            raise _not_found(key)
        return object()

    def remove_object(self, bucket: str, key: str) -> None:
        self._check()
        self.objects.pop(key, None)
