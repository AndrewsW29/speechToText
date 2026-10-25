from pathlib import Path

import pytest
from app.adapters.outbound.pdf.local_object_store import LocalFileObjectStore
from app.application.errors import StorageError


def test_local_store_is_content_addressed_immutable_and_confined_to_its_root(
    tmp_path: Path,
) -> None:
    store = LocalFileObjectStore(tmp_path)
    key = store.put(b"%PDF-1.4 a")
    assert store.put(b"%PDF-1.4 a") == key and store.get(key) == b"%PDF-1.4 a" and store.exists(key)
    store.delete(key)
    assert not store.exists(key)
    with pytest.raises(StorageError):
        store.get("../../etc/passwd")
    with pytest.raises(StorageError):
        store.get("sha256/zz/../../x")
    assert not store.exists("../outside")
