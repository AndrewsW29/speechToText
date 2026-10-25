# Model card: intent and slot model

**Purpose.** Classify a spoken developer request into one of the taxonomy intents and tag entities
(`LANGUAGE`, `FRAMEWORK`, `ARTIFACT`, `LIBRARY`, `VERSION`, `ERROR_CODE`) so retrieval can filter by them.
Not for general chat, sentiment or any non-developer domain: those inputs should be classified `OUT_OF_SCOPE`.

**Owner.** {owner}

## Provenance
- git SHA: {git_sha}
- image digest: {image_digest}
- dataset hash: {dataset_hash}
- seeds: {seeds}

## Hyperparameters
{hyperparameters}

## Metrics (golden set)
{metrics}

## Metrics by slice (macro-F1)
{slices}

## Known failures
{failures}

## Limits
Trained on English utterances only; raw ASR errors on rare technical terms reduce accuracy.
Confidence is calibrated with temperature scaling on a held-out validation split.
