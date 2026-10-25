"""The Great Expectations suites must pass on real data and FAIL on broken data."""

from ml.evaluation.expectations.dataset_suite import (
    build_suite,
    run,
    to_frame,
    validate_all,
    validate_distribution,
)

INTENTS = {"FIND_DOCS", "EXPLAIN_CONCEPT"}


def _row(i: str, text: str, intent: str = "FIND_DOCS") -> dict:
    tokens = text.split()
    return {
        "id": i,
        "tokens": tokens,
        "tags": ["O"] * len(tokens),
        "intent": intent,
        "source": "seed",
    }


def test_real_datasets_pass_every_suite() -> None:
    reports = validate_all()
    assert all(r["success"] for r in reports), [r for r in reports if not r["success"]]


def test_duplicate_ids_and_unknown_intents_fail() -> None:
    frame = to_frame(
        [_row("a", "show docs"), _row("a", "other docs here"), _row("b", "x y", "NOPE")]
    )
    report = run(build_suite("broken", INTENTS), frame)
    assert not report["success"]
    assert any("unique" in f for f in report["failures"]) and any(
        "in_set" in f for f in report["failures"]
    )


def test_high_duplicate_rate_fails() -> None:
    rows = [_row(str(i), "same text here") for i in range(10)]
    assert not run(build_suite("dupes", INTENTS), to_frame(rows))["success"]


def test_leakage_into_forbidden_texts_fails() -> None:
    rows = [_row("a", "find the docs"), _row("b", "show me the guide")]
    clean = run(build_suite("ok", INTENTS, {"unrelated text"}), to_frame(rows))
    leaky = run(build_suite("leak", INTENTS, {"find the docs"}), to_frame(rows))
    assert clean["success"] and not leaky["success"]


def test_label_distribution_flags_dominant_intent() -> None:
    rows = [_row(str(i), f"docs {i}") for i in range(97)] + [
        _row("x", "explain", "EXPLAIN_CONCEPT")
    ] * 3
    problems = validate_distribution(to_frame(rows))
    assert any("FIND_DOCS" in p for p in problems) and any("EXPLAIN_CONCEPT" in p for p in problems)
