"""Step 0: TF-IDF + logistic regression baseline. Sets the floor any neural model must beat.

uv run --group ml-core python -m ml.training.intent.baseline
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from ml.evaluation.run_eval import evaluate
from ml.training.common.datasets import DATA, ML_ROOT, read_jsonl

METRICS_PATH = ML_ROOT / "evaluation" / "baseline_metrics.json"


def train(rows: list[dict[str, Any]]) -> Any:
    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=0),
    )
    model.fit([" ".join(r["tokens"]) for r in rows], [r["intent"] for r in rows])
    return model


def predict(model: Any, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    texts = [" ".join(r["tokens"]) for r in rows]
    proba = model.predict_proba(texts)
    classes = model.classes_
    return [
        {"intent": str(classes[int(np.argmax(p))]), "confidence": float(np.max(p))} for p in proba
    ]


def run() -> dict[str, Any]:
    seed = read_jsonl(DATA / "raw" / "seed.jsonl")
    model = train(seed)
    report = {}
    for name in ("golden", "challenge"):
        rows = read_jsonl(DATA / "golden" / f"{name}.jsonl")
        report[name] = evaluate(rows, predict(model, rows))
    report["trained_on"] = {"file": "raw/seed.jsonl", "rows": len(seed)}
    return report


if __name__ == "__main__":
    result = run()
    METRICS_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    for name in ("golden", "challenge"):
        m = result[name]
        print(
            name,
            {
                k: (round(v, 3) if isinstance(v, float) else v)
                for k, v in m.items()
                if k != "slices"
            },
        )
