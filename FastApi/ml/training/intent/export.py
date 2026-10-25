"""Export a trained model as a numbered TF Serving version directory with its sidecar files."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def next_version(base: Path) -> int:
    if not base.exists():
        return 1
    numbers = [int(p.name) for p in base.iterdir() if p.is_dir() and p.name.isdigit()]
    return max(numbers, default=0) + 1


def export_model(
    model: Any,
    base: Path,
    vocab: Mapping[str, int],
    intents: list[str],
    slot_tags: list[str],
    temperature: float,
    max_len: int,
    metadata: Mapping[str, Any] | None = None,
) -> Path:
    """`base/<version>/` holds saved_model.pb + variables (TF Serving) and the files the API needs:
    vocab.json, labels.json, temperature.json and metadata.json."""
    version_dir = base / str(next_version(base))
    version_dir.parent.mkdir(parents=True, exist_ok=True)
    model.export(str(version_dir))
    (version_dir / "vocab.json").write_text(json.dumps(dict(vocab), ensure_ascii=False))
    (version_dir / "labels.json").write_text(
        json.dumps({"intents": intents, "slot_tags": slot_tags, "max_len": max_len})
    )
    (version_dir / "temperature.json").write_text(json.dumps({"temperature": temperature}))
    (version_dir / "metadata.json").write_text(
        json.dumps(dict(metadata or {}), indent=2, default=str)
    )
    return version_dir
