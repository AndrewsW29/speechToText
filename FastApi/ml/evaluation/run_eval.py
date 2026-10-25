"""Evaluation harness: overall gate metrics plus slice reports.

A prediction is {"intent": str, "confidence": float, "tags": list[str] | None}.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ml.training.common.metrics import ece, entity_f1, macro_f1

MIN_SLICE_SUPPORT = 5


def _length_bucket(record: Mapping[str, Any]) -> str:
    n = len(record["tokens"])
    return "short" if n <= 4 else "medium" if n <= 8 else "long"


def _noise_bucket(record: Mapping[str, Any]) -> str:
    snr = record.get("snr_db")
    if snr is None:
        return "challenge_noisy" if record.get("source") == "challenge" else "clean"
    return "low_snr" if snr < 15 else "high_snr"


def _entity(record: Mapping[str, Any], label: str) -> str:
    for token, tag in zip(record["tokens"], record["tags"], strict=True):
        if tag == f"B-{label}":
            return str(token)
    return "none"


def slice_keys(record: Mapping[str, Any]) -> dict[str, str]:
    return {
        "language": _entity(record, "LANGUAGE"),
        "framework": _entity(record, "FRAMEWORK"),
        "noise": _noise_bucket(record),
        "length": _length_bucket(record),
        "user": str(record.get("user_type", "unknown")),
    }


def slice_report(
    records: Sequence[Mapping[str, Any]], predictions: Sequence[Mapping[str, Any]]
) -> dict[str, float]:
    """Macro-F1 per slice (`dimension=value`), skipping slices with fewer than MIN_SLICE_SUPPORT rows."""
    buckets: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for record, pred in zip(records, predictions, strict=True):
        for dimension, value in slice_keys(record).items():
            buckets[f"{dimension}={value}"].append((record["intent"], pred["intent"]))
    return {
        name: macro_f1([t for t, _ in pairs], [p for _, p in pairs])
        for name, pairs in sorted(buckets.items())
        if len(pairs) >= MIN_SLICE_SUPPORT
    }


def evaluate(
    records: Sequence[Mapping[str, Any]], predictions: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    if len(records) != len(predictions):
        raise ValueError("one prediction per record is required")
    gold = [r["intent"] for r in records]
    pred = [p["intent"] for p in predictions]
    oos = [i for i, g in enumerate(gold) if g == "OUT_OF_SCOPE"]
    metrics: dict[str, Any] = {
        "n": len(records),
        "intent_macro_f1": macro_f1(gold, pred),
        "ood_recall": sum(pred[i] == "OUT_OF_SCOPE" for i in oos) / len(oos) if oos else None,
        "slot_f1": None,
        "ece": None,
        "slices": slice_report(records, predictions),
    }
    if all(p.get("tags") for p in predictions):
        metrics["slot_f1"] = entity_f1(
            [r["tags"] for r in records], [p["tags"] for p in predictions]
        )
    if all("confidence" in p for p in predictions):
        metrics["ece"] = ece(
            [p["confidence"] for p in predictions],
            [g == p for g, p in zip(gold, pred, strict=True)],
        )
    return metrics


def main(argv: Sequence[str]) -> int:  # pragma: no cover - thin CLI
    from ml.training.common.datasets import read_jsonl

    dataset, predictions, out = Path(argv[0]), Path(argv[1]), Path(argv[2])
    metrics = evaluate(read_jsonl(dataset), read_jsonl(predictions))
    out.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in metrics.items() if k != "slices"}, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
