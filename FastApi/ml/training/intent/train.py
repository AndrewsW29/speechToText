"""Train the joint model: class weights, loss weights, early stopping, checkpoints, fixed seeds."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from ml.training.common.datasets import encode


def encode_rows(
    rows: Sequence[Mapping[str, Any]],
    vocab: Mapping[str, int],
    intents: Sequence[str],
    slot_tags: Sequence[str],
    max_len: int,
    weights: Mapping[str, float] | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Return (tokens, targets, sample_weights) as numpy arrays.

    Slot weights mask padding so it never contributes to the loss; intent weights are per class.
    """
    intent_ids = {name: i for i, name in enumerate(intents)}
    tag_ids = {tag: i for i, tag in enumerate(slot_tags)}
    x = np.array([encode(r, vocab, max_len) for r in rows], dtype="int32")
    slots = np.zeros((len(rows), max_len), dtype="int32")
    mask = np.zeros((len(rows), max_len), dtype="float32")
    for i, r in enumerate(rows):
        n = min(len(r["tags"]), max_len)
        slots[i, :n] = [tag_ids[t] for t in r["tags"][:n]]
        mask[i, :n] = 1.0
    labels = np.array([intent_ids[r["intent"]] for r in rows], dtype="int32")
    intent_w = np.array([(weights or {}).get(r["intent"], 1.0) for r in rows], dtype="float32")
    return x, {"intent": labels, "slots": slots}, {"intent": intent_w, "slots": mask}


def train_model(
    config: Any,
    train_rows: Sequence[Mapping[str, Any]],
    val_rows: Sequence[Mapping[str, Any]],
    vocab: Mapping[str, int],
    intents: Sequence[str],
    slot_tags: Sequence[str],
    weights: Mapping[str, float],
    checkpoint_dir: Path,
    log_metrics: Any = None,
) -> tuple[Any, dict[str, list[float]]]:
    import keras

    from ml.training.intent.model import build_joint_model

    keras.utils.set_random_seed(config.seed)
    if config.mixed_precision:
        keras.mixed_precision.set_global_policy("mixed_float16")

    model = build_joint_model(
        len(vocab), len(intents), len(slot_tags), config.max_len, config.dim, config.dropout
    )
    ce = keras.losses.SparseCategoricalCrossentropy(from_logits=True)
    model.compile(
        optimizer=keras.optimizers.Adam(config.learning_rate),
        loss={"intent": ce, "slots": ce},
        loss_weights={"intent": 1.0, "slots": config.slot_loss_weight},
        metrics={"intent": "accuracy", "slots": "accuracy"},
    )
    x, y, w = encode_rows(train_rows, vocab, intents, slot_tags, config.max_len, weights)
    vx, vy, vw = encode_rows(val_rows, vocab, intents, slot_tags, config.max_len, weights)

    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    callbacks: list[Any] = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=config.patience, restore_best_weights=True
        ),
        keras.callbacks.ModelCheckpoint(
            str(checkpoint_dir / "epoch-{epoch:02d}.weights.h5"), save_weights_only=True
        ),
    ]
    if log_metrics is not None:
        callbacks.append(
            keras.callbacks.LambdaCallback(
                on_epoch_end=lambda epoch, logs: log_metrics(logs or {}, epoch)
            )
        )
    history = model.fit(
        x,
        y,
        sample_weight=w,
        validation_data=(vx, vy, vw),
        epochs=config.epochs,
        batch_size=config.batch_size,
        callbacks=callbacks,
        verbose=0,
    )
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    return model, {k: [float(v) for v in vals] for k, vals in history.history.items()}
