import pytest
from app.application.errors import NotAPdfError, QuotaExceededError, TooLargeError
from app.application.pdf.services.validation import PdfLimits, Usage, validate_upload

from tests.pdf_fixtures import build_pdf, zip_renamed_as_pdf

LIMITS = PdfLimits(
    max_file_bytes=10_000, max_documents=3, max_pages_per_day=100, max_storage_bytes=50_000
)
IDLE = Usage(documents=0, pages_today=0, storage_bytes=0)


def test_valid_pdf_passes_and_returns_its_sha256() -> None:
    data = build_pdf()
    result = validate_upload(data, LIMITS, IDLE)
    assert len(result.sha256) == 64 and result.size == len(data)


def test_a_zip_renamed_pdf_is_refused_by_magic_bytes_before_anything_else() -> None:
    with pytest.raises(NotAPdfError, match="valid PDF"):
        validate_upload(zip_renamed_as_pdf(), LIMITS, IDLE)


@pytest.mark.parametrize("claim", [("report.pdf", "application/pdf"), ("evil.exe", "text/plain")])
def test_filename_and_content_type_are_never_trusted(claim: tuple[str, str]) -> None:
    good = build_pdf()
    assert validate_upload(
        good, LIMITS, IDLE, filename=claim[0], content_type=claim[1]
    ).size == len(good)
    with pytest.raises(NotAPdfError):
        validate_upload(
            b"MZ" + b"\x00" * 100,
            LIMITS,
            IDLE,
            filename="report.pdf",
            content_type="application/pdf",
        )


def test_header_may_follow_a_short_preamble_but_not_arbitrary_junk() -> None:
    data = build_pdf()
    assert validate_upload(b"\n\n" + data, LIMITS, IDLE).size
    with pytest.raises(NotAPdfError):
        validate_upload(b"x" * 2048 + data, LIMITS, IDLE)


def test_empty_and_oversized_files_are_refused() -> None:
    with pytest.raises(NotAPdfError):
        validate_upload(b"", LIMITS, IDLE)
    with pytest.raises(TooLargeError):
        validate_upload(build_pdf() + b"\x00" * 20_000, LIMITS, IDLE)


@pytest.mark.parametrize(
    "usage",
    [Usage(3, 0, 0), Usage(0, 100, 0), Usage(0, 0, 49_999)],
    ids=["document-count", "pages-per-day", "storage"],
)
def test_per_user_quotas_are_enforced(usage: Usage) -> None:
    with pytest.raises(QuotaExceededError):
        validate_upload(build_pdf(), LIMITS, usage)


def test_limits_come_from_megabytes_in_settings() -> None:
    from app.config import Settings

    limits = PdfLimits.from_settings(Settings(auth_enabled=False))
    assert limits.max_file_bytes == 50 * 1024 * 1024 and limits.max_pages == 1000
