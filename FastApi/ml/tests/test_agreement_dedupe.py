import pytest

from ml.training.common.agreement import cohen_kappa
from ml.training.common.dedupe import near_duplicates, remove_near_duplicates


def test_kappa_perfect_chance_and_partial() -> None:
    a = ["X", "Y", "X", "Y"]
    assert cohen_kappa(a, a) == 1.0
    assert cohen_kappa(["X", "X", "Y", "Y"], ["X", "Y", "X", "Y"]) == pytest.approx(0.0)
    assert 0 < cohen_kappa(["X", "X", "Y", "Y", "X"], ["X", "X", "Y", "X", "X"]) < 1


def test_kappa_requires_equal_length() -> None:
    with pytest.raises(ValueError):
        cohen_kappa(["X"], ["X", "Y"])


TEXTS = [
    "how do i create a spring controller",
    "how do i create a spring controller please",
    "explain dependency injection",
    "what is the weather today",
]


def test_near_duplicates_use_cosine_similarity() -> None:
    pairs = near_duplicates(TEXTS, threshold=0.8)
    assert (0, 1) in pairs and all(3 not in p for p in pairs)


def test_remove_keeps_first_of_each_cluster() -> None:
    kept = remove_near_duplicates(TEXTS, threshold=0.8)
    assert kept == [0, 2, 3]


def test_custom_embedder_is_used() -> None:
    vectors = {"a": [1.0, 0.0], "b": [1.0, 0.01], "c": [0.0, 1.0]}
    assert near_duplicates(["a", "b", "c"], 0.99, embed=lambda ts: [vectors[t] for t in ts]) == {
        (0, 1)
    }
