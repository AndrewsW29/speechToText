from pathlib import Path

from app.adapters.outbound.stt.glossary_corrected_transcriber import GlossaryCorrectedTranscriber
from app.application.services.glossary import GlossaryCorrector
from app.config import Settings
from app.main import build_container

from tests.fakes import FakeTranscriber

TERMS = Path(__file__).resolve().parents[2] / "ml" / "glossary" / "terms.yaml"


def test_decorator_corrects_the_inner_transcript_and_keeps_the_language() -> None:
    inner = FakeTranscriber("how do I create a rest controller with j p a", language="en")
    result = GlossaryCorrectedTranscriber(inner, GlossaryCorrector.from_yaml(TERMS)).transcribe(
        b"x"
    )
    assert result.text == "how do I create a @RestController with JPA"
    assert result.language is not None and result.language.code == "en"


def test_real_glossary_leaves_everyday_developer_words_alone() -> None:
    corrector = GlossaryCorrector.from_yaml(TERMS)
    for sentence in (
        "take a rest after the service call",
        "the controller calls the service and the repository",
        "write a unit test for the user service",
        "explain how dependency injection works",
    ):
        assert corrector.correct(sentence) == sentence


def test_real_glossary_fixes_common_asr_misspellings() -> None:
    corrector = GlossaryCorrector.from_yaml(TERMS)
    assert corrector.correct("use mock ito with jay unit") == "use Mockito with JUnit"
    assert corrector.correct("is dot net faster than kotlin") == "is .NET faster than Kotlin"


def test_container_wraps_the_transcriber_when_a_glossary_is_configured() -> None:
    container = build_container(Settings(auth_enabled=False, glossary_path=TERMS))
    assert isinstance(container.ask_question._transcriber, GlossaryCorrectedTranscriber)


def test_container_without_glossary_uses_the_plain_transcriber() -> None:
    container = build_container(Settings(auth_enabled=False))
    assert not isinstance(container.ask_question._transcriber, GlossaryCorrectedTranscriber)


def test_container_wires_the_intent_classifier_when_a_model_is_configured(tmp_path) -> None:  # type: ignore[no-untyped-def]
    import json

    from app.adapters.outbound.intent.tf_serving_classifier import TFServingIntentClassifier

    (tmp_path / "vocab.json").write_text(json.dumps({"<pad>": 0, "<unk>": 1}))
    (tmp_path / "labels.json").write_text(
        json.dumps({"intents": ["FIND_DOCS"], "slot_tags": ["O"], "max_len": 4})
    )
    (tmp_path / "temperature.json").write_text(json.dumps({"temperature": 1.0}))
    settings = Settings(
        auth_enabled=False,
        qdrant_url=":memory:",
        intent_serving_url="http://tf:8501",
        intent_model_dir=tmp_path,
    )
    container = build_container(settings)
    assert isinstance(container.ask_question._classifier, TFServingIntentClassifier)
