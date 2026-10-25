import pytest

from ml.training.common.markup import MarkupError, parse_markup, to_record


def test_plain_text_is_tokenised_and_lowercased_with_O_tags() -> None:
    tokens, tags = parse_markup("How do I create it")
    assert tokens == ["how", "do", "i", "create", "it"] and set(tags) == {"O"}


def test_entities_get_bio_tags_including_multiword() -> None:
    tokens, tags = parse_markup(
        "make a [spring boot|FRAMEWORK] [service|ARTIFACT] in [java|LANGUAGE]"
    )
    assert tokens == ["make", "a", "spring", "boot", "service", "in", "java"]
    assert tags == ["O", "O", "B-FRAMEWORK", "I-FRAMEWORK", "B-ARTIFACT", "O", "B-LANGUAGE"]


def test_punctuation_is_stripped_from_tokens() -> None:
    tokens, _ = parse_markup("what is DI? Explain, please.")
    assert tokens == ["what", "is", "di", "explain", "please"]


@pytest.mark.parametrize("bad", ["broken [entity", "x [a|NOPE] y", "[|ARTIFACT]", "unmatched ]"])
def test_bad_markup_is_rejected(bad: str) -> None:
    with pytest.raises(MarkupError):
        parse_markup(bad)


def test_to_record_builds_the_jsonl_schema() -> None:
    rec = to_record("u-1", "CREATE_CODE_ARTIFACT", "make a [service|ARTIFACT]", source="seed")
    assert rec == {
        "id": "u-1",
        "tokens": ["make", "a", "service"],
        "tags": ["O", "O", "B-ARTIFACT"],
        "intent": "CREATE_CODE_ARTIFACT",
        "source": "seed",
    }
