from app.application.services.intent_router import Handler, IntentRouter, default_router
from app.domain.entities import Intent
from app.domain.value_objects import Confidence


def _intent(name: str) -> Intent:
    return Intent(name, Confidence(0.9))


def test_routes_registered_intents_to_their_handler() -> None:
    router = IntentRouter(
        {"FIND_DOCS": Handler("find_docs", needs_retrieval=True)}, Handler("fallback", False)
    )
    assert router.route(_intent("FIND_DOCS")).name == "find_docs"


def test_unknown_intents_use_the_fallback() -> None:
    router = IntentRouter({}, Handler("fallback", needs_retrieval=False))
    assert router.route(_intent("SOMETHING_NEW")).name == "fallback"


def test_default_router_covers_every_taxonomy_intent_with_one_handler_each() -> None:
    from ml.training.common.datasets import load_taxonomy

    taxonomy = load_taxonomy()["intents"]
    router = default_router()
    for name, spec in taxonomy.items():
        assert router.route(_intent(name)).name == spec["handler"], name


def test_meta_and_refusals_skip_retrieval_while_knowledge_intents_use_it() -> None:
    router = default_router()
    assert not router.route(_intent("META_COMMAND")).needs_retrieval
    assert not router.route(_intent("OUT_OF_SCOPE")).needs_retrieval
    for name in (
        "CREATE_CODE_ARTIFACT",
        "EXPLAIN_CONCEPT",
        "FIND_DOCS",
        "DEBUG_ERROR",
        "COMPARE_OPTIONS",
        "MODIFY_PREVIOUS",
    ):
        assert router.route(_intent(name)).needs_retrieval, name
