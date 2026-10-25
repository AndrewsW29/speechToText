from ml.training.intent.ood import OodVerdict, is_out_of_scope

CLASSES = ["CREATE_CODE_ARTIFACT", "OUT_OF_SCOPE", "FIND_DOCS"]


def test_explicit_out_of_scope_class_is_rejected() -> None:
    v = is_out_of_scope([0.05, 0.9, 0.05], CLASSES)
    assert v == OodVerdict(True, "class")


def test_low_calibrated_confidence_is_rejected() -> None:
    assert is_out_of_scope([0.4, 0.3, 0.3], CLASSES, confidence_threshold=0.5) == OodVerdict(
        True, "low_confidence"
    )


def test_weak_retrieval_evidence_is_rejected_even_when_the_model_is_confident() -> None:
    v = is_out_of_scope([0.9, 0.05, 0.05], CLASSES, retrieval_score=0.1, retrieval_threshold=0.3)
    assert v == OodVerdict(True, "no_retrieval_support")


def test_in_scope_requests_pass_all_three_defences() -> None:
    v = is_out_of_scope([0.9, 0.05, 0.05], CLASSES, retrieval_score=0.8, retrieval_threshold=0.3)
    assert v == OodVerdict(False, None)


def test_retrieval_check_is_skipped_when_no_score_is_available() -> None:
    assert not is_out_of_scope([0.9, 0.05, 0.05], CLASSES, retrieval_threshold=0.3).rejected


def test_class_check_is_reported_first() -> None:
    v = is_out_of_scope([0.1, 0.8, 0.1], CLASSES, retrieval_score=0.0, retrieval_threshold=0.3)
    assert v == OodVerdict(True, "class")
