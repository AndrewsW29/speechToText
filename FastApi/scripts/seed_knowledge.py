"""Seed the knowledge base from the bundled corpus.

Usage: VA_QDRANT_URL=http://localhost:6333 uv run python scripts/seed_knowledge.py [directory]
"""

import sys
from pathlib import Path

from app.bootstrap import build_ingestion_facade
from app.config import get_settings

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "ml" / "training" / "seed_corpus"


def main(directory: Path) -> None:
    summary = build_ingestion_facade(get_settings(), allow_local=True).ingest(str(directory))
    print(f"ingested {summary.documents} documents into {summary.chunks} chunks")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DIR)
