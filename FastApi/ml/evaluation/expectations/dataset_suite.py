"""Great Expectations suites for the intent datasets (schema, distribution, empties, duplicates, leakage)."""

from __future__ import annotations

from collections.abc import Collection
from functools import lru_cache

import great_expectations as gx
import pandas as pd

from ml.training.common.datasets import DATA, load_taxonomy, read_jsonl, record_text

MAX_DUPLICATE_RATE = 0.02


@lru_cache
def _context() -> gx.data_context.AbstractDataContext:
    """GE 1.x needs an active context before suites can be built."""
    return gx.get_context(mode="ephemeral")


MIN_INTENT_SHARE, MAX_INTENT_SHARE = 0.04, 0.30


def to_frame(rows: list[dict]) -> pd.DataFrame:  # type: ignore[type-arg]
    return pd.DataFrame(
        {
            "id": [r["id"] for r in rows],
            "intent": [r["intent"] for r in rows],
            "source": [r["source"] for r in rows],
            "text": [record_text(r) for r in rows],
            "n_tokens": [len(r["tokens"]) for r in rows],
            "tags_match": [len(r["tokens"]) == len(r["tags"]) for r in rows],
        }
    )


def build_suite(
    name: str, intents: Collection[str], forbidden_texts: Collection[str] = ()
) -> gx.ExpectationSuite:
    _context()
    e = gx.expectations
    suite = gx.ExpectationSuite(name=name)
    for column in ("id", "intent", "source", "text"):
        suite.add_expectation(e.ExpectColumnValuesToNotBeNull(column=column))
    suite.add_expectation(e.ExpectColumnValuesToBeUnique(column="id"))
    suite.add_expectation(e.ExpectColumnValuesToBeInSet(column="intent", value_set=sorted(intents)))
    suite.add_expectation(
        e.ExpectColumnValuesToBeBetween(column="n_tokens", min_value=1, max_value=64)
    )
    suite.add_expectation(e.ExpectColumnValuesToBeInSet(column="tags_match", value_set=[True]))
    suite.add_expectation(e.ExpectColumnValuesToNotMatchRegex(column="text", regex=r"^\s*$"))
    suite.add_expectation(
        e.ExpectColumnProportionOfUniqueValuesToBeBetween(
            column="text", min_value=1 - MAX_DUPLICATE_RATE, max_value=1.0
        )
    )
    if forbidden_texts:
        suite.add_expectation(
            e.ExpectColumnValuesToNotBeInSet(column="text", value_set=sorted(forbidden_texts))
        )
    return suite


def label_distribution_suite(intents: Collection[str]) -> gx.ExpectationSuite:
    """Seed data only: every intent present with a sane share."""
    _context()
    suite = gx.ExpectationSuite(name="seed_label_distribution")
    suite.add_expectation(
        gx.expectations.ExpectColumnDistinctValuesToEqualSet(
            column="intent", value_set=sorted(intents)
        )
    )
    return suite


def run(suite: gx.ExpectationSuite, frame: pd.DataFrame) -> dict[str, object]:
    context = _context()
    asset = context.data_sources.add_pandas(f"p-{suite.name}").add_dataframe_asset("frame")
    batch = asset.add_batch_definition_whole_dataframe("whole").get_batch(
        batch_parameters={"dataframe": frame}
    )
    result = batch.validate(suite)
    failures = [
        f"{r.expectation_config.type}({r.expectation_config.kwargs.get('column', '')})"
        for r in result.results
        if not r.success
    ]
    return {"suite": suite.name, "success": bool(result.success), "failures": failures}


def validate_distribution(frame: pd.DataFrame) -> list[str]:
    shares = frame["intent"].value_counts(normalize=True)
    return [
        f"intent {name} share {share:.2%} outside [{MIN_INTENT_SHARE:.0%}, {MAX_INTENT_SHARE:.0%}]"
        for name, share in shares.items()
        if not MIN_INTENT_SHARE <= share <= MAX_INTENT_SHARE
    ]


def validate_all() -> list[dict[str, object]]:
    intents = set(load_taxonomy()["intents"])
    seed = read_jsonl(DATA / "raw" / "seed.jsonl")
    golden = read_jsonl(DATA / "golden" / "golden.jsonl")
    challenge = read_jsonl(DATA / "golden" / "challenge.jsonl")
    train_texts = {record_text(r) for r in seed}
    reports = [
        run(build_suite("seed", intents), to_frame(seed)),
        run(label_distribution_suite(intents), to_frame(seed)),
        run(build_suite("golden", intents, train_texts), to_frame(golden)),
        run(build_suite("challenge", intents, train_texts), to_frame(challenge)),
    ]
    problems = validate_distribution(to_frame(seed))
    reports.append({"suite": "seed_intent_shares", "success": not problems, "failures": problems})
    return reports
