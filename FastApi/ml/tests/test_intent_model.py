import numpy as np
import pytest

pytest.importorskip("keras")

from ml.training.intent.model import build_joint_model

V, N_INTENTS, S, L = 50, 8, 13, 12


def _ids(batch: int = 3) -> np.ndarray:
    rng = np.random.default_rng(0)
    x = rng.integers(2, V, size=(batch, L)).astype("int32")
    x[:, 7:] = 0  # padding
    return x


def test_outputs_are_named_per_utterance_and_per_token_logits() -> None:
    out = build_joint_model(V, N_INTENTS, S, max_len=L, dim=16)(_ids(), training=False)
    assert set(out) == {"intent", "slots"}
    assert tuple(out["intent"].shape) == (3, N_INTENTS) and tuple(out["slots"].shape) == (3, L, S)


def test_outputs_are_linear_logits_not_probabilities() -> None:
    out = np.asarray(
        build_joint_model(V, N_INTENTS, S, max_len=L, dim=16)(_ids(), training=False)["intent"]
    )
    assert not np.allclose(out.sum(axis=1), 1.0)  # a softmax head would sum to 1
    assert (out < 0).any() or (out > 1).any()


def test_padding_is_masked_so_sequence_length_does_not_change_the_prediction() -> None:
    short = build_joint_model(V, N_INTENTS, S, max_len=8, dim=16)
    long = build_joint_model(V, N_INTENTS, S, max_len=16, dim=16)
    long.set_weights(short.get_weights())
    base = np.array([[5, 9, 12, 7, 3, 0, 0, 0]], dtype="int32")
    padded = np.concatenate([base, np.zeros((1, 8), dtype="int32")], axis=1)
    a = np.asarray(short(base, training=False)["intent"])
    b = np.asarray(long(padded, training=False)["intent"])
    np.testing.assert_allclose(a, b, atol=1e-5)


def test_changing_only_padded_positions_never_matters() -> None:
    model = build_joint_model(V, N_INTENTS, S, max_len=L, dim=16)
    x = _ids(2)
    y = x.copy()
    y[:, 10:] = 0  # already zero; same tokens
    np.testing.assert_allclose(
        np.asarray(model(x, training=False)["intent"]),
        np.asarray(model(y, training=False)["intent"]),
        atol=1e-6,
    )
