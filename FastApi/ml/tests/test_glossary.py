from app.application.services.glossary import GlossaryCorrector

CORRECTOR = GlossaryCorrector(
    {
        "restcontroller": "@RestController",
        "springboot": "Spring Boot",
        "jpa": "JPA",
        "dotnet": ".NET",
    }
)


def test_spelled_out_acronym_and_phrase_are_corrected() -> None:
    assert CORRECTOR.correct("how do I create a rest controller with j p a") == (
        "how do I create a @RestController with JPA"
    )


def test_ordinary_words_are_left_alone() -> None:
    assert CORRECTOR.correct("take a rest") == "take a rest"
    assert CORRECTOR.correct("how do I use j p a") == "how do I use JPA"


def test_neighbouring_words_are_never_swallowed() -> None:
    assert CORRECTOR.correct("create a rest controller and a service") == (
        "create a @RestController and a service"
    )


def test_matches_never_overlap() -> None:
    out = CORRECTOR.correct("spring boot rest controller")
    assert out == "Spring Boot @RestController"


def test_alias_with_dot_prefix() -> None:
    assert CORRECTOR.correct("is dot net still supported") == "is .NET still supported"


def test_empty_and_unmatched_text() -> None:
    assert CORRECTOR.correct("") == ""
    assert CORRECTOR.correct("nothing to fix here") == "nothing to fix here"


def test_from_yaml_builds_aliases(tmp_path) -> None:  # type: ignore[no-untyped-def]
    f = tmp_path / "terms.yaml"
    f.write_text("terms:\n  - canonical: JPA\n    aliases: [jay pee ay]\n")
    assert GlossaryCorrector.from_yaml(f).correct("learn jay pee ay today") == "learn JPA today"


def test_longest_match_wins_at_equal_score() -> None:
    corrector = GlossaryCorrector({"net": ".NET", "dotnet": ".NET"})
    assert corrector.correct("is dot net ok") == "is .NET ok"


def test_canonical_can_be_excluded_when_it_is_a_common_word(tmp_path) -> None:  # type: ignore[no-untyped-def]
    f = tmp_path / "t.yaml"
    f.write_text(
        'terms:\n  - { canonical: ".NET", aliases: ["dot net"], match_canonical: false }\n'
    )
    c = GlossaryCorrector.from_yaml(f)
    assert c.correct("a safety net") == "a safety net" and c.correct("use dot net") == "use .NET"
