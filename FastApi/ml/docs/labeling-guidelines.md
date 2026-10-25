# Labeling guidelines

One label per utterance for **intent**; BIO tags per token for **entities**. When unsure, ask a second
annotator rather than guessing. Two annotators label a sample; target Cohen's kappa ≥ 0.8
(`ml/training/common/agreement.py`). Disagreements usually mean the taxonomy is unclear, not the annotator.

## Intents (mutually exclusive; each maps to one handler)

| Intent | Use when | Examples | Not this (use instead) |
| :--- | :--- | :--- | :--- |
| `CREATE_CODE_ARTIFACT` | The user wants code produced | "create a controller and a service in java" · "write a dto in kotlin" · "generate a repository with jpa" | "what is a controller" → `EXPLAIN_CONCEPT` |
| `EXPLAIN_CONCEPT` | The user wants to understand something | "what is dependency injection" · "how does lazy loading work" | "show me the docs for lazy loading" → `FIND_DOCS` |
| `FIND_DOCS` | The user wants a reference or link | "show me the docs for spring data jpa" · "find the javadoc for completablefuture" | "explain completablefuture" → `EXPLAIN_CONCEPT` |
| `DEBUG_ERROR` | Something fails and needs a fix | "i get a null pointer exception in my service" · "my controller returns 404" | "what is a 404" → `EXPLAIN_CONCEPT` |
| `COMPARE_OPTIONS` | A choice between named options | "rest controller versus functional endpoints" · "gradle or maven" | "explain gradle" → `EXPLAIN_CONCEPT` |
| `MODIFY_PREVIOUS` | A follow-up that changes the last answer; it only makes sense with history | "now add validation" · "make it use kotlin" | A complete standalone request → its own intent |
| `META_COMMAND` | Controls the app, not the topic | "repeat that" · "save this answer" · "dark mode" | "repeat the loop in java" is `EXPLAIN_CONCEPT`/`CREATE_CODE_ARTIFACT` |
| `OUT_OF_SCOPE` | Not about software development | "what's the weather" · "tune a pid controller" | Anything developer-related, even if odd |

### Boundary cases and hard negatives

- **"controller" alone is ambiguous.** Label `OUT_OF_SCOPE` when the context is a game pad, PID/thermostat, air-traffic or
  remote control; label by intent when the context is MVC/Spring ("my controller returns 404").
- **Words that sound like the domain** are `OUT_OF_SCOPE` when used in their everyday sense: "spring cleaning",
  "service my car", "java coffee", "repository of antiques", "inject insulin".
- **Compound requests** ("explain DI and then write an example"): label the first request; split long utterances in the UI.
- **Follow-ups that restate the topic** ("add validation to the controller") are still `MODIFY_PREVIOUS` when the intent is to
  change the previous answer; if no answer exists yet, label `CREATE_CODE_ARTIFACT`.
- **Spoken numbers**: "five hundred" is an `ERROR_CODE`; "java seventeen" gives `VERSION` for the number.

## Entities (BIO, per token)

`LANGUAGE`, `FRAMEWORK`, `ARTIFACT`, `LIBRARY`, `VERSION`, `ERROR_CODE`. Label the smallest span that names the thing;
multi-word names get `B-` then `I-` ("spring boot" = `B-FRAMEWORK I-FRAMEWORK`). Do not label generic words ("code", "app").
Misrecognized names in ASR text keep the label of the intended entity ("kontroller" is still `ARTIFACT`).

## Process

1. Write markup lines (`INTENT :: text with [entity|LABEL]`) in `ml/data/raw/seed_markup.txt`.
2. `make -C ml data validate` regenerates JSONL and runs the Great Expectations suites.
3. Never edit the golden or challenge sets after freezing; they are checked against `data/golden/CHECKSUMS.json`.
   To change them deliberately, run `python -m ml.training.common.build_data --freeze` and explain why in the PR.
4. Production data enters only with `consent_training`, after PII scrubbing, through the review queue.
