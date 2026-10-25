import os
import time

import numpy as np
import pytest

pytest.importorskip("tensorflow")

from ml.training.intent.export import export_model
from ml.training.intent.model import build_joint_model

BUDGET_MS = float(os.environ.get("INTENT_LATENCY_BUDGET_MS", "50"))


def test_single_utterance_inference_stays_inside_the_budget(tmp_path) -> None:  # type: ignore[no-untyped-def]
    import tensorflow as tf

    model = build_joint_model(8000, 8, 13, max_len=32, dim=128)
    out = export_model(
        model, tmp_path, {"<pad>": 0, "<unk>": 1}, [f"I{i}" for i in range(8)], ["O"] * 13, 1.0, 32
    )
    predict = tf.saved_model.load(str(out)).signatures["serving_default"]
    x = tf.constant(np.random.default_rng(0).integers(2, 8000, size=(1, 32)).astype("int32"))
    for _ in range(5):  # warm-up
        predict(tokens=x)
    timings = []
    for _ in range(40):
        start = time.perf_counter()
        predict(tokens=x)
        timings.append((time.perf_counter() - start) * 1000)
    p95 = float(np.percentile(timings, 95))
    assert p95 < BUDGET_MS, f"p95={p95:.1f}ms exceeds the {BUDGET_MS}ms budget"
