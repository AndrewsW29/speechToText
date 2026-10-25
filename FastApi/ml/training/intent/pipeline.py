"""End-to-end intent/slot training: data -> train -> calibrate -> evaluate -> export -> (register).

uv run --group ml python -m ml.training.intent.pipeline --epochs 30 --seed 7 [--register]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from ml.training.common.datasets import (
    DATA,
    ML_ROOT,
    build_vocab,
    load_taxonomy,
    read_jsonl,
    record_text,
    write_jsonl,
)
from ml.training.common.splits import group_split
from ml.training.common.template_expansion import expand, max_rows_for_share

ARTIFACTS = ML_ROOT / "artifacts"


@dataclass(frozen=True)
class TrainConfig:
    seed: int = 7
    epochs: int = 30
    batch_size: int = 32
    dim: int = 128
    max_len: int = 32
    learning_rate: float = 1e-3
    dropout: float = 0.2
    patience: int = 4
    slot_loss_weight: float = 0.5
    max_synthetic_share: float = 0.4
    val_fraction: float = 0.15
    mixed_precision: bool = False
    tracking_uri: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def build_training_records(
    ml_root: Path, max_synthetic_share: float, seed: int
) -> list[dict[str, Any]]:
    """Hand-written seed data plus capped template expansion; frozen sets are never included."""
    seed_rows = read_jsonl(ml_root / "data/raw/seed.jsonl")
    spec = yaml.safe_load((ml_root / "data/raw/templates.yaml").read_text(encoding="utf-8"))
    held_out = {
        record_text(r)
        for name in ("golden", "challenge")
        for r in read_jsonl(ml_root / f"data/golden/{name}.jsonl")
    }
    seen = {record_text(r) for r in seed_rows}
    hand = Counter(r["intent"] for r in seed_rows)
    rows = list(seed_rows)
    for intent, templates in spec["intents"].items():
        cap = max_rows_for_share(hand[intent], max_synthetic_share)
        for row in expand(templates, spec["slots"], intent, max_rows=None, seed=seed):
            text = record_text(row)
            if text in seen or text in held_out:
                continue
            seen.add(text)
            rows.append(row)
        synthetic = [r for r in rows if r["intent"] == intent and r["source"] == "template"]
        if len(synthetic) > cap:  # deterministic down-sample to the cap
            keep = {
                r["id"]
                for r in sorted(
                    synthetic,
                    key=lambda r: hashlib.sha1(
                        f"{seed}{r['id']}".encode(), usedforsecurity=False
                    ).hexdigest(),
                )[:cap]
            }
            rows = [
                r
                for r in rows
                if r["source"] != "template" or r["intent"] != intent or r["id"] in keep
            ]
    return rows


def split_train_val(
    rows: Sequence[dict[str, Any]], val_fraction: float, seed: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parts = group_split(rows, {"train": 1 - val_fraction, "val": val_fraction}, seed)
    return parts["train"], parts["val"]


def build_label_space(taxonomy: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    intents = sorted(taxonomy["intents"])
    tags = ["O"] + [f"{p}-{label}" for label in sorted(taxonomy["entities"]) for p in ("B", "I")]
    return intents, tags


def class_weights(labels: Sequence[str], classes: Sequence[str]) -> dict[str, float]:
    """Balanced weights: n / (k * count). Rare intents (e.g. DEBUG_ERROR) are not ignored."""
    counts = Counter(labels)
    n, k = len(labels), len(classes)
    return {c: n / (k * counts[c]) if counts[c] else 0.0 for c in classes}


def dataset_hash(rows: Sequence[Mapping[str, Any]]) -> str:
    payload = "\n".join(json.dumps(r, sort_keys=True) for r in sorted(rows, key=lambda r: r["id"]))
    return hashlib.sha256(payload.encode()).hexdigest()


def git_sha() -> str:
    env = os.environ.get("GIT_SHA")
    if env:
        return env
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=ML_ROOT,
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - exercised by hand/CI job
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=TrainConfig.epochs)
    parser.add_argument("--seed", type=int, default=TrainConfig.seed)
    parser.add_argument("--dim", type=int, default=TrainConfig.dim)
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--tracking-uri", default=f"sqlite:///{ARTIFACTS}/mlflow.db")
    args = parser.parse_args(argv)

    from ml.training.intent.run import run_training

    result = run_training(
        TrainConfig(
            seed=args.seed, epochs=args.epochs, dim=args.dim, tracking_uri=args.tracking_uri
        ),
        register=args.register,
    )
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in {"metrics", "history"}},
            indent=2,
            default=str,
        )
    )
    golden = result["metrics"]["golden"]
    print(
        {
            k: (round(v, 3) if isinstance(v, float) else v)
            for k, v in golden.items()
            if k != "slices"
        }
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = [
    "ARTIFACTS",
    "DATA",
    "TrainConfig",
    "asdict",
    "build_label_space",
    "build_training_records",
    "build_vocab",
    "class_weights",
    "dataset_hash",
    "git_sha",
    "load_taxonomy",
    "np",
    "split_train_val",
    "write_jsonl",
]
