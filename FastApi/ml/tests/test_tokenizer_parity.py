"""Training and serving must tokenize identically or the model sees different inputs."""

import pytest
from app.application.services.tokenizer import tokenize as serving_tokenize

from ml.training.common.datasets import read_jsonl
from ml.training.common.markup import tokenize as training_tokenize

SAMPLES = [
    "How do I create a @RestController?",
    "what is DI",
    "docs for spring.io/guides",
    "use .NET 8 please",
    "Explain C++ templates",
    "   leading and trailing   ",
    "dash-separated words and under_scores",
    "",
]


@pytest.mark.parametrize("text", SAMPLES)
def test_serving_tokenizer_matches_training_tokenizer(text: str) -> None:
    assert serving_tokenize(text) == training_tokenize(text)


def test_every_golden_utterance_round_trips(ml_root) -> None:  # type: ignore[no-untyped-def]
    for row in read_jsonl(ml_root / "data/golden/golden.jsonl"):
        text = " ".join(row["tokens"])
        assert serving_tokenize(text) == row["tokens"]
