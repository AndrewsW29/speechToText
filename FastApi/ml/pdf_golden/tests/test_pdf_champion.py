from ml.pdf_golden import compare


def summary(**overrides):
    base = {
        "clean_book": {"reading_order": 0.97, "boilerplate_leakage": 0.005, "chunk_integrity": 0},
        "tables": {"teds": 0.90},
    }
    for key, value in overrides.items():
        s, m = key.split("__")
        base[s][m] = value
    return base


def test_equal_or_better_candidate_is_accepted() -> None:
    verdict = compare.compare(summary(), summary(tables__teds=0.95))
    assert verdict.accepted and not verdict.regressions


def test_loss_within_one_point_is_tolerated() -> None:
    assert compare.compare(summary(), summary(tables__teds=0.895)).accepted


def test_loss_over_one_point_in_one_slice_rejects() -> None:
    verdict = compare.compare(summary(), summary(tables__teds=0.88))
    assert not verdict.accepted
    assert [(r.slice, r.metric) for r in verdict.regressions] == [("tables", "teds")]


def test_lower_is_better_metrics_regress_when_they_grow() -> None:
    bad = compare.compare(summary(), summary(clean_book__boilerplate_leakage=0.06))
    assert [(r.slice, r.metric) for r in bad.regressions] == [("clean_book", "boilerplate_leakage")]
    assert not compare.compare(summary(), summary(clean_book__chunk_integrity=1)).accepted


def test_a_metric_that_became_null_or_a_slice_that_vanished_is_a_regression() -> None:
    assert not compare.compare(summary(), summary(tables__teds=None)).accepted
    missing = summary()
    del missing["tables"]
    assert not compare.compare(summary(), missing).accepted


def test_null_champion_metrics_are_not_compared() -> None:
    assert compare.compare(summary(tables__teds=None), summary(tables__teds=0.1)).accepted
