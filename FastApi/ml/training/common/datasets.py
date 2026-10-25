"""JSONL IO, normalisation, record validation and (lazy) tf.data builders."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

ML_ROOT = Path(__file__).resolve().parents[2]
DATA = ML_ROOT / "data"
TAXONOMY_PATH = DATA / "taxonomy.yaml"
PAD, UNK = "<pad>", "<unk>"
Record = dict[str, Any]


def read_jsonl(path: Path) -> list[Record]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def normalize(text: str) -> str:
    """Canonical form for leakage and duplicate checks: lowercase words only."""
    return " ".join(re.findall(r"[a-z0-9@+#]+", text.lower()))


def record_text(record: Mapping[str, Any]) -> str:
    return normalize(" ".join(record["tokens"]))


def load_taxonomy(path: Path = TAXONOMY_PATH) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def entity_labels(taxonomy: Mapping[str, Any]) -> set[str]:
    return set(taxonomy["entities"])


def valid_tags(taxonomy: Mapping[str, Any]) -> set[str]:
    return {"O"} | {f"{p}-{label}" for label in entity_labels(taxonomy) for p in ("B", "I")}


def validate_record(record: Mapping[str, Any], taxonomy: Mapping[str, Any]) -> list[str]:
    """Return a list of problems (empty when the record is valid)."""
    problems: list[str] = []
    for key in ("id", "tokens", "tags", "intent", "source"):
        if key not in record:
            problems.append(f"missing field {key!r}")
    if problems:
        return problems
    tokens, tags = record["tokens"], record["tags"]
    if len(tokens) != len(tags):
        problems.append("tokens and tags differ in length")
    if not tokens or any(not str(t).strip() for t in tokens):
        problems.append("empty tokens")
    if record["intent"] not in taxonomy["intents"]:
        problems.append(f"unknown intent {record['intent']!r}")
    allowed = valid_tags(taxonomy)
    previous = "O"
    for tag in tags:
        if tag not in allowed:
            problems.append(f"invalid tag {tag!r}")
        elif tag.startswith("I-") and previous not in {f"B-{tag[2:]}", tag}:
            problems.append(f"{tag} does not continue a {tag[2:]} entity")
        previous = tag
    if str(record["source"]).endswith("augmented") and "parent_id" not in record:
        problems.append("augmented record without parent_id")
    return problems


def build_vocab(records: Sequence[Mapping[str, Any]], min_count: int = 1) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        for token in record["tokens"]:
            counts[token] = counts.get(token, 0) + 1
    vocab = {PAD: 0, UNK: 1}
    for token, n in sorted(counts.items()):
        if n >= min_count:
            vocab[token] = len(vocab)
    return vocab


def encode(record: Mapping[str, Any], vocab: Mapping[str, int], max_len: int) -> list[int]:
    ids = [vocab.get(t, vocab[UNK]) for t in record["tokens"]][:max_len]
    return ids + [vocab[PAD]] * (max_len - len(ids))


def to_tf_dataset(  # pragma: no cover - needs TensorFlow (group 'ml')
    records: Sequence[Mapping[str, Any]],
    vocab: Mapping[str, int],
    intents: Sequence[str],
    slot_tags: Sequence[str],
    max_len: int = 32,
    batch_size: int = 32,
    shuffle: bool = False,
) -> Any:
    import tensorflow as tf

    intent_ids = {name: i for i, name in enumerate(intents)}
    tag_ids = {tag: i for i, tag in enumerate(slot_tags)}
    tokens = [encode(r, vocab, max_len) for r in records]
    slots = [
        [tag_ids[t] for t in r["tags"][:max_len]] + [tag_ids["O"]] * (max_len - len(r["tags"]))
        for r in records
    ]
    labels = [intent_ids[r["intent"]] for r in records]
    ds = tf.data.Dataset.from_tensor_slices(
        ({"tokens": tokens}, {"intent": labels, "slots": slots})
    )
    if shuffle:
        ds = ds.shuffle(len(records), seed=0)
    return ds.cache().batch(batch_size).prefetch(tf.data.AUTOTUNE)


def iter_markup(path: Path) -> Iterator[tuple[str, str]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            intent, _, text = line.partition(" :: ")
            yield intent.strip(), text.strip()
