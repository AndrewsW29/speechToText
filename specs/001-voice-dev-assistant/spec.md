# Feature Specification: Voice-Driven Developer Assistant

**Feature Branch**: `001-voice-dev-assistant`

**Created**: 2026-10-24

**Status**: Draft

**Input**: Derived from `FEATURE.md` (Voice-Driven Developer Assistant: Detailed Architecture)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Speak a question and get an answer (Priority: P1) 🎯 MVP

A developer records a spoken question in the web app. The audio is uploaded, transcribed
server-side, and a fixed (walking-skeleton) answer is shown with the transcript.

**Why this priority**: proves the whole path client → API → STT port → answer → client,
and the Docker Compose environment, before any intelligence is added.

**Independent Test**: record audio in the Angular app against the FastAPI service in Docker
Compose; the transcript and an answer are displayed.

**Acceptance Scenarios**:

1. **Given** a recorded WebM/Opus clip, **When** it is posted to `POST /v1/questions`, **Then**
   the response contains a transcript and an answer with at least one source.
2. **Given** an empty or unsupported audio payload, **When** it is posted, **Then** a 422
   Problem Details error is returned without internals leaked.

---

### User Story 2 - Answers grounded in a knowledge base (Priority: P2)

Java and Spring documentation is ingested into the vector database; questions are answered from
the top retrieved chunks (hybrid dense + keyword search, language filter, rerank).

**Why this priority**: gives answers real content and a measurable retrieval quality.

**Independent Test**: ingest a seed corpus, ask "create a controller and service in Java";
the expected `@RestController` / `@Service` chunks are in the top-k (recall@k threshold).

**Acceptance Scenarios**:

1. **Given** an ingested corpus, **When** a Java question is asked, **Then** sources are filtered
   to `language=java` and returned sorted by score descending.
2. **Given** the same document ingested twice, **When** ingestion runs, **Then** no duplicates are
   created (idempotent content-hash IDs).

---

### User Story 3 - Intent and entity understanding (Priority: P3)

A TensorFlow classifier detects intents (`CREATE_CODE_ARTIFACT`, `EXPLAIN_CONCEPT`, `FIND_DOCS`)
and entities (`language`, `artifact`) which drive retrieval filters.

**Why this priority**: improves relevance and enables task-style requests.

**Independent Test**: golden set of 200 labeled utterances reaches the accuracy threshold in CI.

**Acceptance Scenarios**:

1. **Given** "make a Spring service", **When** classified, **Then** intent is `CREATE_CODE_ARTIFACT`
   with `framework=spring`, `artifact=service`.
2. **Given** a new model scoring below the golden-set threshold, **When** CI runs, **Then** it fails.

---

### User Story 4 - Generated answers with graceful degradation (Priority: P4)

A local LLM (Ollama) composes answers from retrieved context; a circuit breaker falls back to
retrieval-only answers when the LLM is slow or down.

**Why this priority**: richer answers without making the LLM a single point of failure.

**Independent Test**: stop the Ollama container; questions still return retrieval-only answers.

**Acceptance Scenarios**:

1. **Given** a healthy LLM, **When** a question is asked, **Then** the answer cites its sources.
2. **Given** repeated LLM timeouts, **When** the breaker opens, **Then** answers degrade to snippets.

---

### User Story 5 - Mobile clients (Priority: P5)

Android (Kotlin/Compose) and iOS (Swift/SwiftUI) apps record audio and use the same API
contract as the web client.

**Why this priority**: extends reach once the contract is stable.

**Independent Test**: each app records, sends audio and renders the answer against the staging API.

**Acceptance Scenarios**:

1. **Given** a signed-in user, **When** they record a question on either app, **Then** the transcript
   and answer render and feedback buttons are offered.

---

### User Story 6 - Feedback and continuous learning (Priority: P6)

Users rate answers (thumbs up/down); a scheduled job builds a training set, retrains intent,
embedding and reranker models, evaluates on the golden set, registers the model and canary-rolls it.

**Why this priority**: makes the system improve with use.

**Independent Test**: submit feedback, trigger the retraining job; a new model version is registered
only if golden-set metrics improve.

**Acceptance Scenarios**:

1. **Given** an answer, **When** feedback is submitted, **Then** it is stored and a
   `FeedbackSubmitted` event is emitted.
2. **Given** low-confidence samples, **When** training data is built, **Then** they await human review.

---

### User Story 7 - Conversation experience (Priority: P7)

Searchable history, saved answers, settings (theme, default context), follow-up suggestions,
read-aloud and share actions, and a live "I heard" caption while speaking, on web, Android and iOS,
following the design in `UX/UI /`.

**Why this priority**: completes the designed experience once the core loop and clients exist.

**Independent Test**: ask two questions, find one via History search, save it, open it under Saved,
switch theme in Settings, and see partial transcripts while speaking.

**Acceptance Scenarios**:

1. **Given** past questions, **When** the user searches History, **Then** matching items are listed
   grouped by day with their context tags.
2. **Given** an answer, **When** the user taps Save, **Then** it appears under Saved on every client.

---

### User Story 8 - Production hardening (Priority: P8)

Kubernetes overlays, autoscaling, observability, security policies and Terraform-provisioned
infrastructure for every app.

**Independent Test**: deploy to a staging cluster via GitOps; probes, HPA, NetworkPolicies and
dashboards behave as specified.

**Acceptance Scenarios**:

1. **Given** a staging cluster, **When** load increases, **Then** stateless services scale out.

### User Stories 9–14 - AI model training and learning loop (Priorities: P9–P14)

Derived from `TRAINING.md` (backend only): US9 ML foundations (datasets, golden sets, harness, baseline,
glossary); US10 intent/slots model v1 with calibration and abstention; US11 retrieval quality, grounded
answers, guardrails, degradation ladder; US12 feedback capture, decision traces, review queue; US13 embedder
and reranker training, automated pipeline, champion/challenger; US14 optional advanced models.
Independent tests and acceptance gates are defined per story in `tasks.md`.

---

### Edge Cases

- Audio too long, silent, corrupt or in an unsupported codec.
- Vector DB, Redis, STT or LLM unavailable (timeouts, retries, degraded responses).
- Low intent confidence: ask for clarification or fall back to `FIND_DOCS`.
- Concurrent duplicate ingestion jobs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept audio from web, Android and iOS clients over HTTPS.
- **FR-002**: System MUST transcribe audio server-side behind a `Transcriber` port.
- **FR-003**: System MUST classify intent and extract entities behind an `IntentClassifier` port.
- **FR-004**: System MUST retrieve with hybrid search, metadata filters and reranking via ports.
- **FR-005**: System MUST generate answers that always include at least one source.
- **FR-006**: System MUST fall back to retrieval-only answers when the LLM is unavailable.
- **FR-007**: System MUST ingest documents asynchronously (Celery) with idempotent chunk IDs.
- **FR-008**: System MUST store feedback and use it for scheduled model retraining with a golden-set gate.
- **FR-009**: System MUST expose an OpenAPI contract from which TypeScript, Kotlin and Swift clients are generated.
- **FR-010**: System MUST authenticate via OAuth2/OIDC (Keycloak) with JWT.
- **FR-011**: Clients MUST contain no business logic.
- **FR-012**: Every app MUST ship Docker, Kubernetes and Terraform assets under its own `deploy/` folder.
- **FR-013**: Clients MUST implement the Idle, Listening and Answer screens from `UX/UI /angular.html`,
  `UX/UI /android.html` and `UX/UI /ios.html` (Angular: rail + history + main + sources layout;
  Android: Material 3 bottom navigation and bottom-sheet listening; iOS: tab bar, large title and sheet).
- **FR-014**: Clients MUST support light and dark themes from the shared design tokens, default to the system setting, and meet WCAG 2.2 AA contrast with ≥ 44px touch targets.
- **FR-015**: Answers MUST render code blocks with a Copy action, source links, Helpful / Not helpful feedback, and Save, Share and Read-aloud actions.
- **FR-016**: Listening MUST show a waveform, an auto-stop countdown with Cancel/Done, honor reduced-motion, and (web) support `Ctrl+Shift+M` / `Esc`.
- **FR-018**: Models MUST learn only offline from reviewed, consented, PII-scrubbed data and reach production only through quality gates, shadow/canary and alias promotion; no live weight updates.
- **FR-019**: Every trained model MUST record git SHA, image digest, dataset hash, seeds, hyperparameters and metrics, and ship a model card.
- **FR-020**: Golden and challenge sets MUST be frozen, never used for training, and split by group (`parent_id`) to prevent leakage; gates MUST also check slice regressions.
- **FR-021**: The system MUST answer, clarify or abstain from calibrated confidence and missing entities, and MUST return a degradation-ladder level when dependencies fail.
- **FR-017**: System MUST provide history search, saved answers, user preferences, follow-up suggestions and streamed partial transcripts.

### Key Entities

- **Query**, **Intent**, **KnowledgeChunk**, **Answer** (never without sources), **Feedback**.
- Value objects: **Transcript**, **Language**, **Embedding**, **Confidence**.

## Success Criteria *(mandatory)*

- **SC-001**: Audio-to-answer p95 latency ≤ 5 s for clips ≤ 15 s (retrieval-only path).
- **SC-002**: Intent accuracy on the golden set ≥ 90% (threshold configurable in CI).
- **SC-003**: Retrieval recall@5 ≥ 85% on the known-question set.
- **SC-004**: STT word-error-rate ≤ 15% on the recorded samples.
- **SC-005**: ≥ 80% line/branch coverage on domain and application code.
- **SC-006**: 0 critical/high findings from image, dependency and IaC scans.

## Assumptions

- Server-side STT (faster-whisper) is the default; on-device STT is a later adapter.
- Knowledge source for the first release is public Java/Spring documentation.
- The backend stays on Python; thresholds above are initial and revisable.
- Open decision from FEATURE.md: generated text vs retrieved snippets only is resolved as
  "both, with retrieval-only fallback" (US4).
