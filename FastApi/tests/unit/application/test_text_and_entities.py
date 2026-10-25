from app.application.services.entity_decoder import decode_entities
from app.application.services.tokenizer import tokenize


def test_tokenizer_lowercases_and_drops_punctuation() -> None:
    assert tokenize("What is DI? Explain, please.") == ["what", "is", "di", "explain", "please"]
    assert tokenize("use spring.io and @RestController") == [
        "use",
        "spring.io",
        "and",
        "@restcontroller",
    ]


def test_decode_entities_joins_multiword_spans_and_keeps_the_first_of_each_label() -> None:
    tokens = ["make", "a", "spring", "boot", "service", "in", "java", "or", "kotlin"]
    tags = [
        "O",
        "O",
        "B-FRAMEWORK",
        "I-FRAMEWORK",
        "B-ARTIFACT",
        "O",
        "B-LANGUAGE",
        "O",
        "B-LANGUAGE",
    ]
    assert decode_entities(tokens, tags) == {
        "FRAMEWORK": "spring boot",
        "ARTIFACT": "service",
        "LANGUAGE": "java",
    }


def test_decode_ignores_dangling_inside_tags_and_length_mismatch() -> None:
    assert decode_entities(["a", "b"], ["I-LANGUAGE", "O"]) == {}
    assert decode_entities(["a", "b", "c"], ["B-LANGUAGE"]) == {"LANGUAGE": "a"}
    assert decode_entities([], []) == {}
