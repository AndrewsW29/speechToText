"""Stage metrics and gates of the PDF ingestion quality harness (US17, F50).

Pure functions over ground-truth blocks and a pipeline's output. A pipeline `Block` is a dict with
`kind`, `text`, `page` and optionally `rows`; a `Chunk` has `id`, `text`, `pages`; a citation has `page`
(0-based index), `quote` and `chunk_id`. Metrics that cannot be computed are `None` (never 0), and
`None` fails its gate.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher

import jiwer
from apted import APTED, Config
from apted.helpers import Tree

from ml.training.common.metrics import recall_at_k

Block = dict
_WS = re.compile(r"\s+")


def norm(text: str) -> str:
    return _WS.sub(" ", text).strip()


def cer(ref: str, hyp: str) -> float:
    """Character error rate."""
    if not ref:
        return 0.0 if not hyp else 1.0
    if not hyp:
        return 1.0
    return float(jiwer.cer(ref, hyp))


def scan_cer(gt_blocks: Sequence[Block], pred_blocks: Sequence[Block]) -> float:
    """CER weighted by length; each gt block is scored against its closest block on the same page."""
    err = total = 0.0
    for g in gt_blocks:
        ref = norm(g["text"])
        cands = [norm(p["text"]) for p in pred_blocks if p.get("page", g["page"]) == g["page"]]
        best = min((cer(ref, c) for c in cands), default=1.0)
        err += best * len(ref)
        total += len(ref)
    return err / total if total else 0.0


def _locate(gt_text: str, pred: Sequence[Block]) -> int | None:
    """Index of the pred block that carries a gt block: exact text first, then containing it."""
    want = norm(gt_text)
    for i, p in enumerate(pred):
        if norm(p.get("text", "")) == want:
            return i
    for i, p in enumerate(pred):
        if want in norm(p.get("text", "")):
            return i
    return None


def reading_order_accuracy(gt_blocks: Sequence[Block], pred_blocks: Sequence[Block]) -> float:
    """Share of gt block pairs (i before j) that the pipeline emits in the same order.

    A pair with a missing block, or with both blocks merged into one, counts as wrong.
    """
    pos = [_locate(g["text"], pred_blocks) for g in gt_blocks]
    pairs = right = 0
    for i in range(len(pos)):
        for j in range(i + 1, len(pos)):
            pairs += 1
            if pos[i] is not None and pos[j] is not None and pos[i] < pos[j]:
                right += 1
    return right / pairs if pairs else 1.0


class _Cfg(Config):
    def rename(self, n1: Tree, n2: Tree) -> float:
        (t1, x1), (t2, x2) = n1.name, n2.name
        if t1 != t2:
            return 1.0
        return 0.0 if x1 == x2 else 1.0 - SequenceMatcher(None, x1, x2).ratio()

    def children(self, node: Tree) -> list[Tree]:
        return node.children


def _tree(rows: Sequence[Sequence[str]]) -> Tree:
    root = Tree(("table", ""))
    for row in rows:
        tr = Tree(("tr", ""))
        tr.children = [Tree(("td", norm(str(cell)))) for cell in row]
        root.children.append(tr)
    return root


def _size(t: Tree) -> int:
    return 1 + sum(_size(c) for c in t.children)


def teds(gt_rows: Sequence[Sequence[str]], pred_rows: Sequence[Sequence[str]]) -> float:
    """Tree-edit-distance similarity of two tables (1 identical, 0 nothing in common)."""
    if not pred_rows:
        return 0.0
    a, b = _tree(gt_rows), _tree(pred_rows)
    dist = APTED(a, b, _Cfg()).compute_edit_distance()
    return max(0.0, 1.0 - dist / max(_size(a), _size(b)))


def table_teds(gt_blocks: Sequence[Block], pred_blocks: Sequence[Block]) -> float:
    """Mean TEDS over the gt tables, each matched with its best unused pred table."""
    gold = [b for b in gt_blocks if b["kind"] == "table"]
    pool = [p for p in pred_blocks if p.get("kind") == "table" and p.get("rows")]
    scores = []
    for g in gold:
        best, idx = 0.0, None
        for i, p in enumerate(pool):
            s = teds(g["rows"], p["rows"])
            if s > best:
                best, idx = s, i
        if idx is not None:
            pool.pop(idx)
        scores.append(best)
    return sum(scores) / len(scores) if scores else 1.0


def code_fidelity(gt_blocks: Sequence[Block], pred_blocks: Sequence[Block]) -> float:
    """Share of gt code blocks reproduced exactly (whitespace included) as a code block."""
    gold = [b["text"] for b in gt_blocks if b["kind"] == "code"]
    got = {p["text"] for p in pred_blocks if p.get("kind") == "code"}
    return sum(g in got for g in gold) / len(gold) if gold else 1.0


def boilerplate_leakage(chunks: Sequence[Block], boilerplate: Collection[str]) -> float:
    """Share of chunks that contain a repeated header or footer."""
    if not chunks:
        return 0.0
    bad = sum(any(b in c["text"] for b in boilerplate) for c in chunks)
    return bad / len(chunks)


def chunk_integrity_violations(gt_blocks: Sequence[Block], chunks: Sequence[Block]) -> int:
    """Code or table blocks split across chunks, plus chunks that cross sections."""
    texts = [c["text"] for c in chunks]
    ntexts = [norm(t) for t in texts]
    violations = 0
    for b in gt_blocks:
        if b["kind"] == "code":
            violations += not any(b["text"] in t for t in texts)
        elif b["kind"] == "table":
            cells = [norm(c) for row in b["rows"] for c in row]
            violations += not any(all(c in t for c in cells) for t in ntexts)
    for t in ntexts:
        sections = {b["section"] for b in gt_blocks if norm(b["text"]) in t}
        violations += len(sections) > 1
    return violations


def _block_for(quote: str, page: int, gt_blocks: Sequence[Block]) -> str | None:
    q = norm(quote)
    if not q:
        return None
    same = [b for b in gt_blocks if b["page"] == page]
    for b in [*same, *gt_blocks]:
        if q in norm(b["text"]):
            return b["id"]
    return None


def citation_accuracy(
    questions: Sequence[dict], answers: dict, gt_blocks: Sequence[Block]
) -> float:
    """Share of questions whose top citation names a page that contains the quoted text."""
    ok = 0
    for q in questions:
        cites = answers.get(q["id"]) or []
        if not cites:
            continue
        top = cites[0]
        quote = norm(top.get("quote", ""))
        ok += bool(quote) and any(
            quote in norm(b["text"]) for b in gt_blocks if b["page"] == top.get("page")
        )
    return ok / len(questions) if questions else 1.0


def recall_at_5(questions: Sequence[dict], answers: dict, gt_blocks: Sequence[Block]) -> float:
    ranked = [
        [
            _block_for(c.get("quote", ""), c.get("page", -1), gt_blocks) or "?"
            for c in answers.get(q["id"]) or []
        ]
        for q in questions
    ]
    return recall_at_k(ranked, [{q["block_id"]} for q in questions], 5) if questions else 1.0


def hidden_text_recall(hidden_texts: Sequence[str], pred_blocks: Sequence[Block]) -> float:
    """Share of injected hidden strings that the pipeline quarantined (kind == "hidden")."""
    if not hidden_texts:
        return 1.0
    caught = " ".join(norm(p["text"]).lower() for p in pred_blocks if p.get("kind") == "hidden")
    return sum(norm(h).lower().rstrip(".") in caught for h in hidden_texts) / len(hidden_texts)


def hidden_false_positive_rate(pred_blocks: Sequence[Block]) -> float:
    """Share of blocks wrongly flagged hidden (on scans this must be ~0: an OCR layer is not hidden)."""
    if not pred_blocks:
        return 0.0
    return sum(p.get("kind") == "hidden" for p in pred_blocks) / len(pred_blocks)


# ---------------------------------------------------------------- gates

BORN_DIGITAL = frozenset({"clean_book", "two_column", "tables", "code", "slides", "mixed_language"})
ALL_SLICES = BORN_DIGITAL | {"clean_scan", "phone_photo", "broken_huge", "adversarial"}


@dataclass(frozen=True)
class Gate:
    op: str
    threshold: float
    slices: frozenset[str]

    def passes(self, value: float) -> bool:
        return {
            ">=": value >= self.threshold,
            "<=": value <= self.threshold,
            "==": value == self.threshold,
        }[self.op]


GATES: dict[str, Gate] = {
    "cer": Gate("<=", 0.03, frozenset({"clean_scan"})),
    "reading_order": Gate(">=", 0.95, BORN_DIGITAL),
    "teds": Gate(">=", 0.85, frozenset({"tables"})),
    "code_fidelity": Gate(">=", 0.95, frozenset({"code"})),
    "boilerplate_leakage": Gate("<=", 0.01, frozenset({"clean_book", "two_column", "slides"})),
    "chunk_integrity": Gate("==", 0, BORN_DIGITAL | {"broken_huge"}),
    "citation_accuracy": Gate(">=", 0.98, ALL_SLICES),
    "recall_at_5": Gate(">=", 0.85, ALL_SLICES),
    "hidden_text_recall": Gate(">=", 0.95, frozenset({"adversarial"})),
    "hidden_false_positive_rate": Gate("<=", 0.01, frozenset({"clean_scan", "phone_photo"})),
}


@dataclass(frozen=True)
class GateResult:
    slice: str
    metric: str
    value: float | None
    threshold: float
    passed: bool


def evaluate_gates(summary: dict[str, dict]) -> list[GateResult]:
    """One result per (metric, slice) cell of the gate table; null or missing values fail."""
    out = []
    for metric, gate in GATES.items():
        for s in sorted(gate.slices):
            value = summary.get(s, {}).get(metric)
            out.append(
                GateResult(
                    s, metric, value, gate.threshold, value is not None and gate.passes(value)
                )
            )
    return out
