import hashlib
import json
from pathlib import Path

import pikepdf
import pypdfium2 as pdfium
import pytest

from ml.pdf_golden import build_corpus

PKG = Path(__file__).resolve().parents[1]
SLICES = [
    "clean_book",
    "two_column",
    "tables",
    "code",
    "clean_scan",
    "phone_photo",
    "slides",
    "mixed_language",
    "broken_huge",
    "adversarial",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def doc_files(corpus: tuple[Path, dict]) -> list[Path]:
    out, gt = corpus
    return [out / d["file"] for g in gt.values() for d in g["documents"]]


def page_text(path: Path, index: int) -> str:
    return pdfium.PdfDocument(str(path))[index].get_textpage().get_text_range()


def test_all_ten_slices_exist_with_purpose_and_pdfs(corpus) -> None:
    out, gt = corpus
    assert list(gt) == SLICES
    for name, g in gt.items():
        assert g["purpose"], name
        for d in g["documents"]:
            assert (out / d["file"]).stat().st_size > 0
            assert d["blocks"], d["file"]


def test_build_is_deterministic_across_two_builds(corpus, tmp_path) -> None:
    _, gt = corpus
    again = build_corpus.build_all(tmp_path)
    assert again == gt
    for path in doc_files(corpus):
        assert sha(path) == sha(tmp_path / path.name), path.name


def test_committed_ground_truth_matches_the_builder_and_checksums(corpus) -> None:
    _, gt = corpus
    checks = json.loads((PKG / "CHECKSUMS.json").read_text())
    for name, g in gt.items():
        committed = PKG / "ground_truth" / f"{name}.json"
        assert json.loads(committed.read_text()) == g, f"{name}: re-run make pdf-corpus"
        assert checks[f"ground_truth/{name}.json"] == sha(committed)
    assert checks["schema.json"] == sha(PKG / "schema.json")


def test_ground_truth_follows_the_schema(corpus) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((PKG / "schema.json").read_text())
    for g in corpus[1].values():
        jsonschema.validate(g, schema)


def test_block_pages_and_questions_are_consistent(corpus) -> None:
    for g in corpus[1].values():
        for d in g["documents"]:
            ids = {b["id"] for b in d["blocks"]}
            assert len(ids) == len(d["blocks"])
            assert all(0 <= b["page"] < d["pages"] for b in d["blocks"])
            for q in d["questions"]:
                assert q["block_id"] in ids and 0 <= q["page"] < d["pages"]


def test_generated_pdfs_are_not_committed() -> None:
    assert ".build/" in (PKG / ".gitignore").read_text()
    assert not list(PKG.glob("ground_truth/*.pdf"))


def test_clean_book_has_roman_page_labels_and_repeated_furniture(corpus) -> None:
    out, gt = corpus
    d = gt["clean_book"]["documents"][0]
    with pikepdf.open(out / d["file"]) as pdf:
        labels = pdf.Root.PageLabels.Nums
        assert str(labels[1].S) == "/r"
    assert d["page_labels"][:3] == ["i", "ii", "1"]
    for i in range(d["pages"]):
        text = page_text(out / d["file"], i)
        assert all(b in text for b in d["boilerplate"])


def test_two_column_ground_truth_reads_left_column_first(corpus) -> None:
    d = corpus[1]["two_column"]["documents"][0]
    page0 = [b for b in d["blocks"] if b["page"] == 0 and b["kind"] == "paragraph"]
    assert [b["column"] for b in page0] == sorted(b["column"] for b in page0)
    assert {b["column"] for b in page0} == {0, 1}


def test_tables_have_rows_and_ruled_lines(corpus) -> None:
    d = corpus[1]["tables"]["documents"][0]
    tables = [b for b in d["blocks"] if b["kind"] == "table"]
    assert len(tables) >= 3 and all(len(t["rows"]) >= 4 for t in tables)


def test_code_is_ascii_in_ground_truth_but_curly_and_ligatured_in_the_pdf(corpus) -> None:
    out, gt = corpus
    d = gt["code"]["documents"][0]
    code = [b for b in d["blocks"] if b["kind"] == "code"]
    assert code and all(b["text"].isascii() for b in code)
    pdf_text = "".join(page_text(out / d["file"], i) for i in range(d["pages"]))
    assert "\u201c" in pdf_text  # pdfium expands the ligature on extraction; the fonts prove it
    fonts = " ".join(_fonts(out / d["file"]))
    assert "Courier" in fonts and "Vera" in fonts


def _fonts(path: Path) -> list[str]:
    with pikepdf.open(path) as pdf:
        return [str(f.BaseFont) for p in pdf.pages for f in p.Resources.Font.values()]


@pytest.mark.parametrize("name", ["clean_scan", "phone_photo"])
def test_scans_are_image_only(corpus, name) -> None:
    out, gt = corpus
    d = gt[name]["documents"][0]
    assert page_text(out / d["file"], 0).strip() == ""
    with pikepdf.open(out / d["file"]) as pdf:
        assert len(pdf.pages[0].images) == 1


def test_clean_scan_is_300_dpi(corpus) -> None:
    out, gt = corpus
    d = gt["clean_scan"]["documents"][0]
    with pikepdf.open(out / d["file"]) as pdf:
        page = pdf.pages[0]
        img = next(iter(page.images.values()))
        inches = float(page.MediaBox[2]) / 72
        assert round(int(img.Width) / inches) == 300


def test_slides_have_a_figure_and_a_caption(corpus) -> None:
    kinds = {b["kind"] for b in corpus[1]["slides"]["documents"][0]["blocks"]}
    assert {"figure", "caption", "heading"} <= kinds


def test_mixed_language_has_a_spanish_appendix(corpus) -> None:
    langs = [b["lang"] for b in corpus[1]["mixed_language"]["documents"][0]["blocks"]]
    assert {"en", "es"} == set(langs) and langs[-1] == "es"


def test_broken_and_huge(corpus) -> None:
    out, gt = corpus
    docs = {d["file"]: d for d in gt["broken_huge"]["documents"]}
    broken = out / next(f for f in docs if f.endswith("_broken.pdf"))
    huge = out / next(f for f in docs if f.endswith("_huge.pdf"))
    data = broken.read_bytes()
    offset = int(data.rsplit(b"startxref", 1)[1].split()[0])
    assert offset > len(data)  # the xref pointer is damaged
    assert len(pdfium.PdfDocument(str(broken))) >= 1  # but a tolerant reader recovers it
    assert len(pdfium.PdfDocument(str(huge))) == 900


def test_adversarial_has_hidden_text_javascript_and_a_bomb(corpus) -> None:
    out, gt = corpus
    d = gt["adversarial"]["documents"][0]
    assert d["hidden_texts"]
    with pikepdf.open(out / d["file"]) as pdf:
        assert "/JavaScript" in str(pdf.Root.OpenAction.S) or "JavaScript" in str(
            pdf.Root.OpenAction
        )
        bomb = next(iter(pdf.pages[0].Resources.XObject.values()))
        assert int(bomb.Width) * int(bomb.Height) > 100_000_000
        assert len(bomb.read_raw_bytes()) < 2_000_000
    assert d["hidden_texts"][0] in page_text(out / d["file"], 0)
