"""Orchestrates one training run. Kept apart from pipeline.py so the pure helpers import without TF."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from ml.evaluation.intent_eval import evaluate_predictor, keras_predictor
from ml.registry.register import register_model
from ml.training.common.datasets import ML_ROOT, build_vocab, load_taxonomy, read_jsonl
from ml.training.intent.calibrate import fit_temperature
from ml.training.intent.export import export_model
from ml.training.intent.pipeline import (
    ARTIFACTS,
    TrainConfig,
    build_label_space,
    build_training_records,
    class_weights,
    dataset_hash,
    git_sha,
    split_train_val,
)
from ml.training.intent.train import encode_rows, train_model


def _epoch_logger(tracking_uri: str | None) -> Any:
    if not tracking_uri:
        return None
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    import mlflow

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("intent-training")
    run = mlflow.start_run(run_name=f"train-{int(time.time())}")

    def log(logs: dict[str, float], epoch: int) -> None:
        mlflow.log_metrics(
            {k: float(v) for k, v in logs.items()}, step=epoch, run_id=run.info.run_id
        )

    return log


def run_training(config: TrainConfig, register: bool = False) -> dict[str, Any]:
    taxonomy = load_taxonomy()
    rows = build_training_records(ML_ROOT, config.max_synthetic_share, config.seed)
    train_rows, val_rows = split_train_val(rows, config.val_fraction, config.seed)
    intents, slot_tags = build_label_space(taxonomy)
    vocab = build_vocab(train_rows)  # train only: validation/golden words stay unknown
    weights = class_weights([r["intent"] for r in train_rows], intents)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    log = _epoch_logger(config.tracking_uri)
    model, history = train_model(
        config,
        train_rows,
        val_rows,
        vocab,
        intents,
        slot_tags,
        weights,
        ARTIFACTS / "checkpoints" / stamp,
        log,
    )
    if log is not None:
        import mlflow

        mlflow.end_run()

    vx, vy, _ = encode_rows(val_rows, vocab, intents, slot_tags, config.max_len)
    val_logits = np.asarray(model(vx, training=False)["intent"])
    temperature = fit_temperature(val_logits, vy["intent"])  # validation data only

    predictor = keras_predictor(model, vocab, intents, slot_tags, temperature, config.max_len)
    golden = evaluate_predictor(predictor, read_jsonl(ML_ROOT / "data/golden/golden.jsonl"))
    challenge = evaluate_predictor(predictor, read_jsonl(ML_ROOT / "data/golden/challenge.jsonl"))
    metrics = {"golden": golden, "challenge": challenge}

    data_hash = dataset_hash(train_rows)
    metadata = {
        "git_sha": git_sha(),
        "image_digest": os.environ.get("IMAGE_DIGEST", ""),
        "dataset_hash": data_hash,
        "seeds": {"python": config.seed, "keras": config.seed, "split": config.seed},
        "hyperparameters": {k: v for k, v in asdict(config).items() if k != "extra"},
        "metrics": {k: v for k, v in golden.items() if v is not None},
    }
    version_dir = export_model(
        model,
        ARTIFACTS / "intent",
        vocab,
        intents,
        slot_tags,
        temperature,
        config.max_len,
        metadata={**metadata, "epochs_run": len(history["loss"]), "train_rows": len(train_rows)},
    )
    candidate = ARTIFACTS / "candidate"
    candidate.mkdir(parents=True, exist_ok=True)
    (candidate / "metrics.json").write_text(
        json.dumps(golden, indent=2, sort_keys=True, default=float) + "\n"
    )
    (candidate / "challenge_metrics.json").write_text(
        json.dumps(challenge, indent=2, sort_keys=True) + "\n"
    )
    (candidate / "VERSION").write_text(version_dir.name)

    registered = None
    if register:
        registered = register_model(
            metadata,
            version_dir,
            tracking_uri=config.tracking_uri or f"sqlite:///{ARTIFACTS}/mlflow.db",
        )
    return {
        "version_dir": str(version_dir),
        "temperature": temperature,
        "epochs_run": len(history["loss"]),
        "dataset_hash": data_hash,
        "train_rows": len(train_rows),
        "val_rows": len(val_rows),
        "registered_version": registered,
        "metrics": metrics,
        "history": history,
    }


__all__ = ["Path", "run_training"]
