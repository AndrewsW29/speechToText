"""Behaviour every ObjectStore must have: content-addressed, immutable, honest about failures."""

import hashlib

import pytest
from app.adapters.outbound.pdf.minio_object_store import MinioObjectStore
from app.application.errors import StorageError
from app.application.pdf.ports.object_store import ObjectStore

from tests.fakes.minio import FakeMinio
from tests.fakes.pdf import InMemoryObjectStore
from tests.pdf_fixtures import build_pdf


@pytest.fixture(params=["memory", "minio"])
def store(request: pytest.FixtureRequest) -> ObjectStore:
    return (
        InMemoryObjectStore()
        if request.param == "memory"
        else MinioObjectStore(FakeMinio(), "documents")
    )


def test_key_is_derived_from_the_sha256_and_roundtrips(store: ObjectStore) -> None:
    data = build_pdf(2)
    key = store.put(data)
    assert hashlib.sha256(data).hexdigest() in key
    assert store.get(key) == data and store.exists(key)


def test_putting_the_same_content_twice_is_idempotent(store: ObjectStore) -> None:
    data = build_pdf()
    assert store.put(data) == store.put(data)


def test_different_content_gets_different_keys(store: ObjectStore) -> None:
    assert store.put(build_pdf(1)) != store.put(build_pdf(2))


def test_missing_objects_raise_storage_errors_and_delete_is_safe(store: ObjectStore) -> None:
    with pytest.raises(StorageError):
        store.get("sha256/nope")
    assert not store.exists("sha256/nope")
    store.delete("sha256/nope")
    key = store.put(b"%PDF-1.4 x")
    store.delete(key)
    assert not store.exists(key)


def test_minio_never_overwrites_an_existing_original() -> None:
    client = FakeMinio()
    store = MinioObjectStore(client, "documents")
    data = build_pdf()
    store.put(data)
    store.put(data)
    assert client.put_calls == 1


def test_minio_connection_errors_become_transient_storage_errors() -> None:
    client = FakeMinio(fail=True)
    with pytest.raises(StorageError):
        MinioObjectStore(client, "documents").put(build_pdf())


def test_stored_bytes_are_streamed_with_their_length() -> None:
    client = FakeMinio()
    MinioObjectStore(client, "documents").put(b"%PDF-1.4 abc")
    assert client.last_length == len(b"%PDF-1.4 abc")
