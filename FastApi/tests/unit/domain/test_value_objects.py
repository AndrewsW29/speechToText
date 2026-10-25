import dataclasses

import pytest
from app.domain.value_objects import Confidence, Embedding, Language, Transcript


class TestLanguage:
    def test_normalizes_to_lowercase(self) -> None:
        assert Language("EN").code == "en"

    @pytest.mark.parametrize("bad", ["", "  ", "english-us-long"])
    def test_rejects_invalid_codes(self, bad: str) -> None:
        with pytest.raises(ValueError):
            Language(bad)


class TestTranscript:
    def test_holds_text_and_language(self) -> None:
        t = Transcript(text="how do I create a controller", language=Language("en"))
        assert t.text == "how do I create a controller"
        assert t.language == Language("en")

    def test_strips_whitespace(self) -> None:
        assert Transcript(text="  hi  ").text == "hi"

    def test_rejects_empty_text(self) -> None:
        with pytest.raises(ValueError):
            Transcript(text="   ")

    def test_is_immutable(self) -> None:
        t = Transcript(text="hi")
        with pytest.raises(dataclasses.FrozenInstanceError):
            t.text = "other"  # type: ignore[misc]


class TestEmbedding:
    def test_exposes_dimension(self) -> None:
        assert Embedding((0.1, 0.2, 0.3)).dimension == 3

    def test_rejects_empty_vector(self) -> None:
        with pytest.raises(ValueError):
            Embedding(())


class TestConfidence:
    @pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
    def test_accepts_unit_interval(self, value: float) -> None:
        assert Confidence(value).value == value

    @pytest.mark.parametrize("value", [-0.01, 1.01])
    def test_rejects_out_of_range(self, value: float) -> None:
        with pytest.raises(ValueError):
            Confidence(value)
