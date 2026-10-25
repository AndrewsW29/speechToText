"""Build JSONL datasets from the hand-written markup files and freeze the golden sets.

uv run --group ml-core python -m ml.training.common.build_data [--freeze]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from ml.training.common.datasets import DATA, iter_markup, write_jsonl
from ml.training.common.markup import to_record

SOURCES = {
    DATA / "raw" / "seed_markup.txt": (DATA / "raw" / "seed.jsonl", "seed", "u"),
    DATA / "golden" / "golden_markup.txt": (DATA / "golden" / "golden.jsonl", "golden", "g"),
    DATA / "golden" / "challenge_markup.txt": (
        DATA / "golden" / "challenge.jsonl",
        "challenge",
        "c",
    ),
}
CHECKSUMS = DATA / "golden" / "CHECKSUMS.json"
FROZEN = ("golden.jsonl", "challenge.jsonl")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict[str, int]:
    counts = {}
    for markup, (target, source, prefix) in SOURCES.items():
        rows = [
            to_record(f"{prefix}-{i:05d}", intent, text, source)
            for i, (intent, text) in enumerate(iter_markup(markup), start=1)
        ]
        counts[target.name] = write_jsonl(target, rows)
    return counts


def freeze() -> None:
    checksums = {name: sha256(DATA / "golden" / name) for name in FROZEN}
    CHECKSUMS.write_text(json.dumps(checksums, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    print(build())
    if "--freeze" in sys.argv:
        freeze()
        print(f"froze {', '.join(FROZEN)}")
