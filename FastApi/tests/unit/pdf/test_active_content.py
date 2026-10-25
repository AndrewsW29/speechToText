import pikepdf
import pytest
from app.adapters.outbound.pdf.active_content import detect_active_content, strip_active_content

from tests.pdf_fixtures import build_pdf


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"javascript": True}, {"javascript"}),
        ({"launch": True}, {"launch"}),
        ({"embedded_file": True}, {"embedded_file"}),
        (
            {"javascript": True, "launch": True, "embedded_file": True},
            {"javascript", "launch", "embedded_file"},
        ),
        ({}, set()),
    ],
)
def test_active_content_is_detected_without_executing_anything(
    kwargs: dict, expected: set[str]
) -> None:
    assert detect_active_content(build_pdf(**kwargs)) == expected


def test_stripping_removes_every_kind_and_keeps_the_pages() -> None:
    hostile = build_pdf(3, javascript=True, launch=True, embedded_file=True)
    clean = strip_active_content(hostile)
    assert detect_active_content(clean) == set()
    with pikepdf.open(__import__("io").BytesIO(clean)) as pdf:
        assert len(pdf.pages) == 3


def test_strip_is_a_no_op_for_clean_files() -> None:
    assert detect_active_content(strip_active_content(build_pdf(2))) == set()


def test_detection_survives_a_damaged_file_by_reporting_nothing_rather_than_crashing() -> None:
    from tests.pdf_fixtures import damaged_xref

    assert isinstance(detect_active_content(damaged_xref()), set)
