from pathlib import Path

import pytest

ML = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def ml_root() -> Path:
    return ML
