import pytest

from ml.training.common.template_expansion import expand

TEMPLATES = ["how do I {create|make|generate} a {ARTIFACT} in {LANGUAGE}"]
SLOTS = {"ARTIFACT": ["controller", "service", "repository"], "LANGUAGE": ["java", "kotlin"]}


def test_expansion_is_slots_times_phrasings_with_bio_labels() -> None:
    rows = expand(TEMPLATES, SLOTS, intent="CREATE_CODE_ARTIFACT", max_rows=None, seed=0)
    assert len(rows) == 3 * 3 * 2
    first = next(r for r in rows if r["tokens"][4:] == ["a", "controller", "in", "java"])
    assert first["tags"][-1] == "B-LANGUAGE" and first["tags"][-3] == "B-ARTIFACT"
    assert all(r["source"] == "template" and r["intent"] == "CREATE_CODE_ARTIFACT" for r in rows)


def test_cap_limits_synthetic_share_of_the_intent() -> None:
    rows = expand(TEMPLATES, SLOTS, intent="X", max_rows=5, seed=0)
    assert len(rows) == 5 and len({r["id"] for r in rows}) == 5


def test_cap_from_share_and_hand_written_count() -> None:
    from ml.training.common.template_expansion import max_rows_for_share

    assert max_rows_for_share(hand_written=60, max_share=0.4) == 40  # 40/(60+40)=0.4
    with pytest.raises(ValueError):
        max_rows_for_share(60, 1.0)


def test_unknown_slot_is_an_error() -> None:
    with pytest.raises(KeyError):
        expand(["make a {MISSING}"], SLOTS, intent="X", max_rows=None, seed=0)
