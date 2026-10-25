"""Trace replay for ingestion: compare chunk ids and citations between pipeline versions (US17, F50).

A trace is what `run_pdf_eval` stores in `traces.json`: chunk ids per document and the citations per
question. Before the index alias flips to a new pipeline version, replaying the stored trace must show
that citations are unchanged and chunk ids churned within budget.

    python -m ml.pdf_golden.replay old/traces.json new/traces.json [--max-churn 0.1]
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CitationChange:
    key: str
    old: list[tuple]
    new: list[tuple]


@dataclass
class ReplayReport:
    chunk_churn: float
    citation_changes: list[CitationChange] = field(default_factory=list)
    max_chunk_churn: float = 0.1

    @property
    def safe(self) -> bool:
        return not self.citation_changes and self.chunk_churn <= self.max_chunk_churn


def _cites(items: list[dict]) -> list[tuple]:
    return [(c.get("page"), c.get("quote")) for c in items]


def compare_traces(old: dict, new: dict, max_chunk_churn: float = 0.1) -> ReplayReport:
    old_ids = {i for ids in old.get("chunks", {}).values() for i in ids}
    new_ids = {i for ids in new.get("chunks", {}).values() for i in ids}
    churn = len(old_ids - new_ids) / len(old_ids) if old_ids else 0.0
    changes = []
    for key, cites in old.get("citations", {}).items():
        before, after = _cites(cites), _cites(new.get("citations", {}).get(key, []))
        if before != after:
            changes.append(CitationChange(key, before, after))
    return ReplayReport(churn, changes, max_chunk_churn)


def save_trace(trace: dict, path: Path) -> None:
    path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n")


def load_trace(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("old", type=Path)
    ap.add_argument("new", type=Path)
    ap.add_argument("--max-churn", type=float, default=0.1)
    args = ap.parse_args()
    report = compare_traces(load_trace(args.old), load_trace(args.new), args.max_churn)
    for c in report.citation_changes:
        print(f"CITATION CHANGED {c.key}: {c.old} -> {c.new}")
    print(
        f"chunk id churn {report.chunk_churn:.1%}; {'safe to flip the alias' if report.safe else 'do NOT flip'}"
    )
    return 0 if report.safe else 1


if __name__ == "__main__":
    raise SystemExit(main())
