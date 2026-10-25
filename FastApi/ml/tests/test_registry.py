import pytest

from ml.registry.register import (
    MissingMetadataError,
    ModelMetadata,
    register_model,
    render_model_card,
)

GOOD = {
    "git_sha": "abc1234",
    "image_digest": "sha256:" + "0" * 64,
    "dataset_hash": "d" * 64,
    "seeds": {"python": 7, "keras": 7},
    "hyperparameters": {"dim": 128, "lr": 0.001},
    "metrics": {"intent_macro_f1": 0.91, "slot_f1": 0.88, "slices": {"language=java": 0.93}},
}


@pytest.mark.parametrize("missing", sorted(GOOD))
def test_registration_is_refused_when_metadata_is_missing(missing: str, tmp_path) -> None:  # type: ignore[no-untyped-def]
    metadata = {k: v for k, v in GOOD.items() if k != missing}
    with pytest.raises(MissingMetadataError) as err:
        register_model(metadata, tmp_path, tracking_uri=f"sqlite:///{tmp_path}/mlflow.db")
    assert missing in str(err.value)


@pytest.mark.parametrize("empty", ["git_sha", "dataset_hash", "seeds", "metrics"])
def test_empty_values_count_as_missing(empty: str, tmp_path) -> None:  # type: ignore[no-untyped-def]
    metadata = {**GOOD, empty: "" if isinstance(GOOD[empty], str) else {}}
    with pytest.raises(MissingMetadataError):
        register_model(metadata, tmp_path, tracking_uri=f"sqlite:///{tmp_path}/mlflow.db")


def test_model_card_summarises_purpose_data_metrics_slices_failures_and_owner() -> None:
    card = render_model_card(
        ModelMetadata.from_dict(GOOD), owner="ml-team", known_failures=["fast speech"]
    )
    for needle in (
        "intent",
        "dddddddd",
        "0.91",
        "language=java",
        "fast speech",
        "ml-team",
        "abc1234",
    ):
        assert needle in card


def test_valid_metadata_registers_a_version_with_an_alias(tmp_path) -> None:  # type: ignore[no-untyped-def]
    pytest.importorskip("mlflow")
    (tmp_path / "artifact").mkdir()
    (tmp_path / "artifact" / "labels.json").write_text("{}")
    uri = f"sqlite:///{tmp_path}/mlflow.db"
    version = register_model(
        GOOD, tmp_path / "artifact", tracking_uri=uri, model_name="intent-test"
    )
    assert version == "1"
    from mlflow import MlflowClient

    client = MlflowClient(tracking_uri=uri, registry_uri=uri)
    assert str(client.get_model_version_by_alias("intent-test", "challenger").version) == "1"
    assert client.get_model_version("intent-test", "1").tags["git_sha"] == "abc1234"
