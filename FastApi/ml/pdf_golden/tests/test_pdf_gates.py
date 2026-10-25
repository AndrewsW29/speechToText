"""Quality gates over the candidate metrics. Marked `gates`: RED on purpose until each stage lands.

Run them with `make -C FastApi/ml pdf-gates` (build the corpus and run `pdf-eval` first). The default
test run deselects them. With the default NotImplementedPipeline every metric is null, so all fail.
"""

import json
from pathlib import Path

import pytest

from ml.pdf_golden import metrics as m

pytestmark = pytest.mark.gates

PKG = Path(__file__).resolve().parents[1]
SUMMARY = PKG / ".build" / "metrics" / "summary.json"
CELLS = [(s, g) for g, gate in m.GATES.items() for s in sorted(gate.slices)]


def load() -> dict:
    assert SUMMARY.exists(), f"{SUMMARY} missing: run `make pdf-corpus pdf-eval` first"
    return json.loads(SUMMARY.read_text())


@pytest.mark.parametrize(("slice_name", "metric"), CELLS, ids=[f"{s}-{g}" for s, g in CELLS])
def test_gate(slice_name: str, metric: str) -> None:
    value = load().get(slice_name, {}).get(metric)
    gate = m.GATES[metric]
    assert value is not None, f"{slice_name}.{metric} is not measured yet (stage missing)"
    assert gate.passes(value), f"{slice_name}.{metric}={value} violates {gate.op} {gate.threshold}"
