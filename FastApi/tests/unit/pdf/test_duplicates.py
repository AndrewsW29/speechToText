from app.application.pdf.use_cases.upload_document import UploadDocument
from app.config import Settings

from tests.fakes.pdf import FakeLauncher, InMemoryDocuments, InMemoryObjectStore
from tests.pdf_fixtures import build_pdf


def _upload() -> tuple[UploadDocument, InMemoryDocuments, FakeLauncher, InMemoryObjectStore]:
    repo, launcher, store = InMemoryDocuments(), FakeLauncher(), InMemoryObjectStore()
    return (
        UploadDocument(store, repo, launcher, Settings(auth_enabled=False)),
        repo,
        launcher,
        store,
    )


def test_first_upload_creates_a_queued_document_and_launches_the_pipeline() -> None:
    uc, repo, launcher, _ = _upload()
    result = uc.execute("user:a", build_pdf(), filename="guide.pdf")
    assert (
        result.duplicate_of is None
        and result.document.status.value == "queued"
        and result.document.version == 1
    )
    assert launcher.launched == [result.document.id] and len(repo.all()) == 1


def test_the_same_file_from_the_same_owner_returns_the_existing_document_without_reprocessing() -> (
    None
):
    uc, repo, launcher, store = _upload()
    data = build_pdf(2)
    first = uc.execute("user:a", data)
    second = uc.execute("user:a", data)
    assert second.document.id == first.document.id and second.duplicate_of == first.document.id
    assert (
        len(repo.all()) == 1 and launcher.launched == [first.document.id] and store.put_count == 1
    )


def test_another_owner_gets_their_own_document_even_for_identical_bytes() -> None:
    uc, _, launcher, _ = _upload()
    data = build_pdf()
    a, b = uc.execute("user:a", data), uc.execute("user:b", data)
    assert a.document.id != b.document.id and b.duplicate_of is None and len(launcher.launched) == 2


def test_quotas_count_the_owners_existing_documents() -> None:
    from app.application.errors import QuotaExceededError

    settings = Settings(auth_enabled=False, pdf_quotas={"max_documents": 1})
    repo, launcher, store = InMemoryDocuments(), FakeLauncher(), InMemoryObjectStore()
    uc = UploadDocument(store, repo, launcher, settings)
    uc.execute("user:a", build_pdf(1))
    try:
        uc.execute("user:a", build_pdf(2))
    except QuotaExceededError:
        pass
    else:
        raise AssertionError("quota not enforced")


def test_a_failed_launch_is_surfaced_and_leaves_a_failed_document() -> None:
    uc, repo, _, _ = _upload()
    uc._launcher = FakeLauncher(fail=True)
    try:
        uc.execute("user:a", build_pdf())
    except Exception as exc:
        assert "queue" in str(exc).lower()
    assert repo.all()[0].status.value == "failed"
