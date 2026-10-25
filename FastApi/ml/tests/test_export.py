import json

import numpy as np
import pytest

pytest.importorskip("tensorflow")

from ml.training.intent.export import export_model, next_version
from ml.training.intent.model import build_joint_model

VOCAB = {"<pad>": 0, "<unk>": 1, "make": 2, "service": 3}
INTENTS = ["A", "B"]
TAGS = ["O", "B-LANGUAGE", "I-LANGUAGE"]


def test_versions_are_numbered_directories(tmp_path) -> None:  # type: ignore[no-untyped-def]
    assert next_version(tmp_path) == 1
    (tmp_path / "3").mkdir()
    (tmp_path / "notes").mkdir()
    assert next_version(tmp_path) == 4
    assert next_version(tmp_path / "missing") == 1


def test_export_writes_a_serving_ready_version_directory(tmp_path) -> None:  # type: ignore[no-untyped-def]
    model = build_joint_model(len(VOCAB), len(INTENTS), len(TAGS), max_len=6, dim=8)
    out = export_model(
        model,
        tmp_path,
        vocab=VOCAB,
        intents=INTENTS,
        slot_tags=TAGS,
        temperature=1.8,
        max_len=6,
        metadata={"git_sha": "abc"},
    )
    assert out.name == "1" and (out / "saved_model.pb").exists() and (out / "variables").is_dir()
    assert json.loads((out / "temperature.json").read_text()) == {"temperature": 1.8}
    assert json.loads((out / "vocab.json").read_text()) == VOCAB
    labels = json.loads((out / "labels.json").read_text())
    assert labels == {"intents": INTENTS, "slot_tags": TAGS, "max_len": 6}
    assert json.loads((out / "metadata.json").read_text())["git_sha"] == "abc"
    assert export_model(model, tmp_path, VOCAB, INTENTS, TAGS, 1.0, 6).name == "2"


def test_exported_model_serves_the_same_logits_through_its_signature(tmp_path) -> None:  # type: ignore[no-untyped-def]
    import tensorflow as tf

    model = build_joint_model(len(VOCAB), len(INTENTS), len(TAGS), max_len=6, dim=8)
    out = export_model(model, tmp_path, VOCAB, INTENTS, TAGS, 1.0, 6)
    x = np.array([[2, 3, 0, 0, 0, 0]], dtype="int32")
    served = tf.saved_model.load(str(out)).signatures["serving_default"](tokens=tf.constant(x))
    np.testing.assert_allclose(
        served["intent"].numpy(), np.asarray(model(x, training=False)["intent"]), atol=1e-5
    )
    assert served["slots"].shape == (1, 6, len(TAGS))
