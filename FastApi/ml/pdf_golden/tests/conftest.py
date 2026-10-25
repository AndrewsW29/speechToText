from pathlib import Path

import pytest

from ml.pdf_golden import build_corpus

PKG = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def corpus(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict]:
    """The corpus built once per session: (directory with the PDFs, ground truth by slice)."""
    out = tmp_path_factory.mktemp("corpus")
    return out, build_corpus.build_all(out)
