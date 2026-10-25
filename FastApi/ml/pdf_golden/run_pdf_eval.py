"""Runs a pipeline under test over the golden corpus and writes `metrics.json` per slice (US17, F50).

    python -m ml.pdf_golden.run_pdf_eval [--pipeline null|oracle|module:Class] [--corpus DIR] [--out DIR]

The default `NotImplementedPipeline` makes every metric null, so the gates are RED on purpose until
the real reader, chunker and answerer exist.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
from typing import Protocol

from ml.pdf_golden import metrics as m

PKG = Path(__file__).resolve().parent


class PipelineUnderTest(Protocol):
    def read(self, pdf_path: Path) -> list[dict]:
        """PDF -> blocks (`kind`, `text`, `page`, optional `rows`, `section`; hidden text is kind "hidden")."""

    def chunk(self, blocks: list[dict]) -> list[dict]:
        """Blocks -> chunks (`id`, `text`, `pages`)."""

    def answer(self, question: str, doc: dict) -> list[dict]:
        """Question about `doc` (`slice`, `file`, `path`) -> ranked citations (`page`, `quote`, `chunk_id`)."""


class NotImplementedPipeline:
    """The default: no stage exists yet, so every metric is null and every gate is red."""

    def read(self, pdf_path: Path) -> list[dict]:
        raise NotImplementedError("reader stage not built yet")

    def chunk(self, blocks: list[dict]) -> list[dict]:
        raise NotImplementedError("chunker stage not built yet")

    def answer(self, question: str, doc: dict) -> list[dict]:
        raise NotImplementedError("answer stage not built yet")


def chunk_id(section: str, text: str) -> str:
    return "c-" + hashlib.sha1(f"{section}|{text}".encode()).hexdigest()[:12]  # noqa: S324


def oracle_chunks(blocks: list[dict]) -> list[dict]:
    """One chunk per section; code and tables stay whole."""
    groups: dict[str, list[dict]] = {}
    for b in blocks:
        if b.get("kind") != "hidden":
            groups.setdefault(b.get("section", ""), []).append(b)
    out = []
    for section, bs in groups.items():
        text = "\n\n".join(b["text"] for b in bs)
        out.append(
            {
                "id": chunk_id(section, text),
                "text": text,
                "pages": sorted({b["page"] for b in bs}),
                "section": section,
            }
        )
    return out


class OraclePipeline:
    """Answers from the ground truth: proves the harness can score perfectly."""

    def __init__(self, gt: dict[str, dict]) -> None:
        self.docs = {d["file"]: d for g in gt.values() for d in g["documents"]}
        self.by_question = {
            (d["file"], q["question"]): (d, q) for d in self.docs.values() for q in d["questions"]
        }

    def _blocks(self, d: dict) -> list[dict]:
        blocks = copy.deepcopy(d["blocks"])
        blocks += [
            {"id": f"h{i}", "page": i % d["pages"], "kind": "hidden", "text": t, "section": ""}
            for i, t in enumerate(d["hidden_texts"])
        ]
        return blocks

    def read(self, pdf_path: Path) -> list[dict]:
        return self._blocks(self.docs[Path(pdf_path).name])

    def chunk(self, blocks: list[dict]) -> list[dict]:
        return oracle_chunks(blocks)

    def answer(self, question: str, doc: dict) -> list[dict]:
        d, q = self.by_question[(doc["file"], question)]
        cid = next((c["id"] for c in oracle_chunks(d["blocks"]) if q["quote"] in c["text"]), "")
        return [{"page": q["page"], "quote": q["quote"], "chunk_id": cid}]


def _try(fn, *args):
    try:
        return fn(*args)
    except NotImplementedError:
        return None


def evaluate_document(
    pipeline: PipelineUnderTest, slice_name: str, d: dict, pdf: Path
) -> tuple[dict, dict, dict]:
    """Returns (metrics, chunk ids, citations by question id) for one PDF."""
    blocks = _try(pipeline.read, pdf)
    chunks = _try(pipeline.chunk, blocks) if blocks is not None else None
    answers: dict | None = {}
    doc = {"slice": slice_name, "file": d["file"], "path": str(pdf)}
    for q in d["questions"]:
        cites = _try(pipeline.answer, q["question"], doc)
        if cites is None:
            answers = None
            break
        answers[q["id"]] = cites
    gb = d["blocks"]
    candidates = {
        "cer": lambda: m.scan_cer(gb, blocks),
        "reading_order": lambda: m.reading_order_accuracy(gb, blocks),
        "teds": lambda: m.table_teds(gb, blocks),
        "code_fidelity": lambda: m.code_fidelity(gb, blocks),
        "boilerplate_leakage": lambda: m.boilerplate_leakage(chunks, d["boilerplate"]),
        "chunk_integrity": lambda: m.chunk_integrity_violations(gb, chunks),
        "citation_accuracy": lambda: m.citation_accuracy(d["questions"], answers, gb),
        "recall_at_5": lambda: m.recall_at_5(d["questions"], answers, gb),
        "hidden_text_recall": lambda: m.hidden_text_recall(d["hidden_texts"], blocks),
        "hidden_false_positive_rate": lambda: m.hidden_false_positive_rate(blocks),
    }
    needs = {
        "boilerplate_leakage": chunks,
        "chunk_integrity": chunks,
        "citation_accuracy": answers,
        "recall_at_5": answers,
    }
    out = {}
    for name, gate in m.GATES.items():
        if slice_name not in gate.slices:
            continue
        ready = needs.get(name, blocks) is not None
        out[name] = candidates[name]() if ready else None
    ids = [c["id"] for c in chunks] if chunks is not None else []
    return out, {"ids": ids}, answers or {}


def _merge(per_doc: list[dict]) -> dict:
    out: dict = {}
    for name in per_doc[0]:
        vals = [p[name] for p in per_doc]
        if any(v is None for v in vals):
            out[name] = None
        elif name == "chunk_integrity":
            out[name] = sum(vals)
        else:
            out[name] = sum(vals) / len(vals)
    return out


def _run(pipeline: PipelineUnderTest, corpus: Path, gt: dict[str, dict]) -> tuple[dict, dict]:
    summary: dict = {}
    trace: dict = {"chunks": {}, "citations": {}}
    for name, g in gt.items():
        per_doc = []
        for d in g["documents"]:
            metrics, chunks, answers = evaluate_document(pipeline, name, d, corpus / d["file"])
            per_doc.append(metrics)
            trace["chunks"][f"{name}/{d['file']}"] = chunks["ids"]
            for qid, cites in answers.items():
                trace["citations"][f"{name}/{d['file']}::{qid}"] = cites
        summary[name] = _merge(per_doc)
    return summary, trace


def evaluate_corpus(pipeline: PipelineUnderTest, corpus: Path, gt: dict[str, dict]) -> dict:
    return _run(pipeline, corpus, gt)[0]


def run(
    pipeline: PipelineUnderTest, corpus: Path, out: Path, gt: dict[str, dict] | None = None
) -> dict:
    """Evaluate and write `<out>/<slice>/metrics.json`, `summary.json` and `traces.json`."""
    gt = gt if gt is not None else load_ground_truth()
    summary, trace = _run(pipeline, corpus, gt)
    for name, metrics in summary.items():
        (out / name).mkdir(parents=True, exist_ok=True)
        (out / name / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "traces.json").write_text(json.dumps(trace, indent=2) + "\n")
    return summary


def load_ground_truth() -> dict[str, dict]:
    return {
        p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in sorted((PKG / "ground_truth").glob("*.json"))
    }


def load_pipeline(spec: str) -> PipelineUnderTest:
    if spec == "null":
        return NotImplementedPipeline()
    if spec == "oracle":
        return OraclePipeline(load_ground_truth())
    module, _, attr = spec.partition(":")
    return getattr(importlib.import_module(module), attr)()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pipeline", default="null", help="null | oracle | module:Class")
    ap.add_argument("--corpus", type=Path, default=PKG / ".build" / "corpus")
    ap.add_argument("--out", type=Path, default=PKG / ".build" / "metrics")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    summary = run(load_pipeline(args.pipeline), args.corpus, args.out)
    measured = sum(v is not None for s in summary.values() for v in s.values())
    print(
        f"metrics written to {args.out} ({measured} measured, {sum(len(s) for s in summary.values()) - measured} null)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
