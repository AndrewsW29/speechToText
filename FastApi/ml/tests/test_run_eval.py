import pytest

from ml.evaluation.run_eval import evaluate, slice_keys, slice_report


def _rec(i: int, intent: str, tokens: list[str], tags: list[str] | None = None, **extra) -> dict:
    return {
        "id": str(i),
        "tokens": tokens,
        "tags": tags or ["O"] * len(tokens),
        "intent": intent,
        "source": "golden",
        **extra,
    }


RECORDS = [
    _rec(
        i,
        "CREATE_CODE_ARTIFACT",
        ["make", "a", "service", "in", "java"],
        ["O", "O", "B-ARTIFACT", "O", "B-LANGUAGE"],
    )
    for i in range(6)
] + [_rec(10 + i, "OUT_OF_SCOPE", ["weather", "today"]) for i in range(6)]


def _preds(intents: list[str], conf: float = 0.9) -> list[dict]:
    return [{"intent": i, "confidence": conf} for i in intents]


def test_perfect_predictions() -> None:
    m = evaluate(RECORDS, _preds([r["intent"] for r in RECORDS]))
    assert m["intent_macro_f1"] == 1.0 and m["ood_recall"] == 1.0 and m["n"] == 12
    assert m["slot_f1"] is None  # no tags predicted
    assert m["ece"] == pytest.approx(0.1)  # confidence 0.9, accuracy 1.0


def test_ood_recall_counts_only_out_of_scope_rows() -> None:
    preds = _preds(["CREATE_CODE_ARTIFACT"] * 6 + ["OUT_OF_SCOPE"] * 3 + ["FIND_DOCS"] * 3)
    assert evaluate(RECORDS, preds)["ood_recall"] == 0.5


def test_slot_f1_uses_predicted_tags() -> None:
    preds = [{"intent": r["intent"], "confidence": 1.0, "tags": r["tags"]} for r in RECORDS]
    assert evaluate(RECORDS, preds)["slot_f1"] == 1.0


def test_slice_report_splits_by_language_length_and_noise() -> None:
    preds = _preds([r["intent"] for r in RECORDS])
    report = slice_report(RECORDS, preds)
    assert report["language=java"] == 1.0 and report["language=none"] == 1.0
    assert report["length=short"] == 1.0 and report["length=medium"] == 1.0
    assert "noise=clean" in report


def test_small_slices_are_omitted() -> None:
    rows = [_rec(1, "FIND_DOCS", ["a"], snr_db=5.0)]
    assert slice_report(rows, _preds(["FIND_DOCS"])) == {}


def test_slice_keys_for_noisy_audio_and_challenge() -> None:
    assert slice_keys(_rec(1, "X", ["a"], snr_db=5.0))["noise"] == "low_snr"
    assert slice_keys(_rec(1, "X", ["a"], snr_db=25.0))["noise"] == "high_snr"
    assert slice_keys({**_rec(1, "X", ["a"]), "source": "challenge"})["noise"] == "challenge_noisy"


def test_one_prediction_per_record() -> None:
    with pytest.raises(ValueError):
        evaluate(RECORDS, [])
