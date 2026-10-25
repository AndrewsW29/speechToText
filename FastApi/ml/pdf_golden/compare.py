"""Champion/challenger comparison: no slice may regress more than one point (US17, F50, P16).

python -m ml.pdf_golden.compare champion/summary.json challenger/summary.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

MAX_REGRESSION = 0.01  # one point
LOWER_IS_BETTER = frozenset(
    {"cer", "boilerplate_leakage", "chunk_integrity", "hidden_false_positive_rate"}
)
COUNTS = frozenset({"chunk_integrity"})  # a count: any increase is a regression


@dataclass(frozen=True)
class Regression:
    slice: str
    metric: str
    champion: float
    challenger: float | None


@dataclass
class Verdict:
    regressions: list[Regression] = field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return not self.regressions


def compare(champion: dict, challenger: dict, max_regression: float = MAX_REGRESSION) -> Verdict:
    """Metrics the champion did not measure are skipped; one the challenger lost is a regression."""
    verdict = Verdict()
    for s, metrics in champion.items():
        for name, old in metrics.items():
            if old is None:
                continue
            new = challenger.get(s, {}).get(name)
            if new is None:
                verdict.regressions.append(Regression(s, name, old, None))
                continue
            loss = new - old if name in LOWER_IS_BETTER else old - new
            limit = 0 if name in COUNTS else max_regression
            if loss > limit + 1e-9:
                verdict.regressions.append(Regression(s, name, old, new))
    return verdict


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("champion", type=Path)
    ap.add_argument("challenger", type=Path)
    args = ap.parse_args()
    verdict = compare(
        json.loads(args.champion.read_text()), json.loads(args.challenger.read_text())
    )
    for r in verdict.regressions:
        print(f"REGRESSION {r.slice}.{r.metric}: {r.champion} -> {r.challenger}")
    print("challenger accepted" if verdict.accepted else "challenger rejected")
    return 0 if verdict.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
