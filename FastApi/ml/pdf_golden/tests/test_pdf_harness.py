"""Proof that the harness works: the oracle passes every gate, each degraded pipeline fails its gate."""

import copy
import random

import pytest

from ml.pdf_golden import metrics as m
from ml.pdf_golden import run_pdf_eval as ev


@pytest.fixture(scope="module")
def gt(corpus) -> dict:
    return corpus[1]


def failing(summary: dict) -> set[str]:
    return {r.metric for r in m.evaluate_gates(summary) if not r.passed}


def run(corpus, pipeline) -> dict:
    out, gt = corpus
    return ev.evaluate_corpus(pipeline, out, gt)


class Degraded(ev.OraclePipeline):
    def __init__(self, gt: dict, mode: str) -> None:
        super().__init__(gt)
        self.mode = mode

    def read(self, pdf_path):
        blocks = super().read(pdf_path)
        if self.mode == "shuffle":
            random.Random(3).shuffle(blocks)
        return blocks

    def chunk(self, blocks):
        chunks = super().chunk(blocks)
        if self.mode == "leak":
            for c in chunks:
                c["text"] = "Spring Guide Reference\n" + c["text"]
        if self.mode == "split_code":
            out = []
            for c in chunks:
                lines = c["text"].split("\n")
                if "return" in c["text"] and len(lines) > 3:
                    mid = len(lines) // 2
                    out += [
                        dict(c, id=c["id"] + "a", text="\n".join(lines[:mid])),
                        dict(c, id=c["id"] + "b", text="\n".join(lines[mid:])),
                    ]
                else:
                    out.append(c)
            chunks = out
        return chunks

    def answer(self, question, doc):
        cites = copy.deepcopy(super().answer(question, doc))
        if self.mode == "wrong_page":
            for c in cites:
                c["page"] += 1
        return cites


def test_oracle_passes_every_gate(corpus) -> None:
    summary = run(corpus, ev.OraclePipeline(corpus[1]))
    results = m.evaluate_gates(summary)
    assert results and all(r.passed for r in results), [r for r in results if not r.passed]
    assert summary["clean_scan"]["cer"] == 0.0


def test_not_implemented_pipeline_makes_every_metric_null_and_every_gate_red(corpus) -> None:
    summary = run(corpus, ev.NotImplementedPipeline())
    assert all(v is None for s in summary.values() for v in s.values())
    assert all(not r.passed for r in m.evaluate_gates(summary))


@pytest.mark.parametrize(
    ("mode", "gate"),
    [
        ("leak", "boilerplate_leakage"),
        ("shuffle", "reading_order"),
        ("split_code", "chunk_integrity"),
        ("wrong_page", "citation_accuracy"),
    ],
)
def test_degraded_pipeline_fails_exactly_its_gate(corpus, mode, gate) -> None:
    summary = run(corpus, Degraded(corpus[1], mode))
    assert failing(summary) == {gate}


def test_runner_writes_metrics_json_per_slice(corpus, tmp_path) -> None:
    out, gt = corpus
    summary = ev.run(ev.OraclePipeline(gt), out, tmp_path)
    for name in gt:
        assert (tmp_path / name / "metrics.json").exists()
    assert (tmp_path / "summary.json").exists() and (tmp_path / "traces.json").exists()
    assert set(summary) == set(gt)
