"""Validate every dataset build; exit non-zero on any failure.

uv run --group ml-core python -m ml.evaluation.validate
"""

from __future__ import annotations

import json
import sys

from ml.evaluation.expectations.dataset_suite import validate_all


def main() -> int:
    reports = validate_all()
    print(json.dumps(reports, indent=2))
    return 0 if all(r["success"] for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
