---

description: "Task list for Voice-Driven Developer Assistant"
---

# Tasks: Voice-Driven Developer Assistant

**Input**: Design documents from `/specs/001-voice-dev-assistant/`

**Prerequisites**: plan.md (required), spec.md (required for user stories); source: `FEATURE.md`

**Tests**: INCLUDED. TDD is mandatory (constitution Principle I; FEATURE.md section 6). In every
story, write the tests first and confirm they FAIL before implementing.

**Status note**: Tasks marked `[X]` for `FastApi/` were verified (tests, ruff, mypy, import-linter, Docker build). `[X]` tasks for `Angular/`, `Android/` and `IOS/` (except the iOS theme test, which ran via `swift test`) are written but NOT built or tested on this machine (no Node/Gradle/Android SDK). US16 and US17 were verified (real tusd resumable upload, PostgreSQL migration, Linux sandbox limits in a container, real Newman, kubeconform); not run: real ClamAV, real MinIO, the DVC tracking of the corpus, the nightly compose stack. US15 tasks (T317–T341) were verified with real Newman (official image) against a live API, except the Keycloak token path of the pre-request script, the nightly compose job, Prism and the Postman publisher against the real API (not run here); T342–T344 wait for US6, US7 and US12. US10 tasks (T207–T229) were verified except the TF Serving container, the training image and CI jobs (not run here), and the intent gates are NOT met by the trained model (see completion report). US2 backend tasks (T061–T079) and the US9 data/evaluation tasks (T179–T206) were verified except the real Piper/ffmpeg/Whisper adapters, the TensorFlow `tf.data` builder and DVC (none installed here); the Angular sources panel (T080–T081) is written but unverified. T029 and T030 stay open (see notes in the completion report).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1..US7)
- Paths are relative to the repository root (`/Users/a.silva/Documents/bruno/AI`)

## Path Conventions

- Backend: `FastApi/app/{domain,application,adapters,workers}`, tests in `FastApi/tests/`
- ML workspace: `FastApi/ml/` (data, glossary, prompts, training, evaluation, pipelines, registry, tests); source: `TRAINING.md`
- Design references: `UX/UI /{angular,android,ios}.html` (folder name has a trailing space)
- Android package `com.voiceassistant` (`Android/app/src/main/kotlin/com/voiceassistant/`)
- Web: `Angular/src/app/`; Android: `Android/app/src/`; iOS: `IOS/VoiceAssistant/`
- Each app owns `deploy/docker`, `deploy/k8s`, `deploy/terraform`
- Latest stable versions are pinned at scaffold time (constitution, Technology Baseline)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create backend hexagonal folder skeleton (`domain/`, `application/use_cases/`, `application/ports/`, `adapters/inbound/`, `adapters/outbound/`, `workers/`, `tests/unit|contract|integration`) under `FastApi/`
- [X] T002 Initialize `FastApi/pyproject.toml` with uv, latest stable Python/FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, Celery, Redis, pytest, pytest-asyncio, httpx, hypothesis, testcontainers
- [X] T003 [P] Configure ruff in `FastApi/ruff.toml` and strict mypy in `FastApi/mypy.ini`
- [X] T004 [P] Configure import-linter layer rules (domain ← application ← adapters) in `FastApi/.importlinter`
- [X] T005 [P] Scaffold Angular app (standalone, signals, strict TS, Vitest, Playwright) in `Angular/`
- [X] T006 [P] Scaffold Android app (Kotlin 2.x, Compose, Hilt, version catalog `Android/gradle/libs.versions.toml`, detekt, ktlint) in `Android/`
- [X] T007 [P] Scaffold iOS app (Swift 6, SwiftUI, SPM, SwiftLint, swift-format) in `IOS/`
- [X] T008 [P] Create local stack `FastApi/deploy/docker/docker-compose.yml` (api, celery worker, redis, qdrant, postgres, minio, keycloak, ollama)
- [X] T009 [P] Create OpenAPI 3.1 skeleton with Problem Details error schema in `FastApi/api-contracts/openapi.yaml`
- [X] T010 [P] Create CI workflow (lint → type-check → unit → integration → build → Trivy scan) in `.github/workflows/backend.yml`
- [X] T011 [P] Create pre-commit config (ruff, mypy, secret scan, conventional commits) in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T012 [P] Write failing unit tests for value objects `Transcript`, `Language`, `Embedding`, `Confidence` in `FastApi/tests/unit/domain/test_value_objects.py`
- [X] T013 [P] Write failing unit tests for entities `Query`, `Intent`, `KnowledgeChunk`, `Answer` (Answer rejects empty sources), `Feedback` in `FastApi/tests/unit/domain/test_entities.py`
- [X] T014 [P] Implement frozen value objects in `FastApi/app/domain/value_objects.py`
- [X] T015 Implement entities in `FastApi/app/domain/entities.py` (depends on T014)
- [X] T016 [P] Implement typed settings from environment variables (no hardcoded secrets) in `FastApi/app/config.py`
- [X] T017 [P] Implement RFC 9457 Problem Details error handling and exception mapping in `FastApi/app/adapters/inbound/rest/errors.py`
- [X] T018 [P] Implement structured JSON logging with correlation IDs and OpenTelemetry setup in `FastApi/app/adapters/inbound/rest/observability.py`
- [X] T019 [P] Implement `/health/live` and `/health/ready` endpoints in `FastApi/app/adapters/inbound/rest/health.py`
- [X] T020 [P] Implement OIDC/JWT validation dependency (Keycloak JWKS) in `FastApi/app/adapters/inbound/rest/auth.py`
- [X] T021 [P] Configure SQLAlchemy 2 async engine, session factory and Alembic in `FastApi/app/adapters/outbound/postgres/database.py` and `FastApi/alembic/`
- [X] T022 [P] Configure Celery app with Redis broker in `FastApi/app/workers/celery_app.py`
- [X] T023 Create FastAPI app factory, lifespan and composition root in `FastApi/app/main.py` (depends on T016–T020)
- [X] T024 [P] Create backend multi-stage Dockerfile (slim base pinned by digest, non-root, HEALTHCHECK) in `FastApi/deploy/docker/Dockerfile` and `FastApi/.dockerignore`
- [X] T025 [P] Add Keycloak realm import for local dev in `FastApi/deploy/docker/keycloak/realm.json`
- [X] T026 [P] Document the design inventory (screens Idle/Listening/Answer, components, tokens, platform differences) from `UX/UI /angular.html`, `UX/UI /android.html`, `UX/UI /ios.html` in `specs/001-voice-dev-assistant/design-notes.md`
- [X] T027 [P] Implement Angular design tokens (light/dark CSS variables: bg #F5F6F7/#0A0A0A, surface, ink, muted, primary #205FFF, accent #AA55FF, line, tint; 12px card radius, 999px pills, 44px min target) and load Heebo + JetBrains Mono in `Angular/src/styles/tokens.scss` and `Angular/src/index.html`
- [X] T028 [P] Write failing tests then implement `ThemeService` (light/dark, default from `prefers-color-scheme`, persisted with safe localStorage access, sets `data-theme`) in `Angular/src/app/core/theme/theme.service.ts` and `Angular/src/app/core/theme/theme.service.spec.ts`
- [ ] T029 [P] Implement Android Material 3 theme (light/dark `ColorScheme` from the design tokens, Heebo `Typography`, shapes: 16dp cards, 18dp mic, 28dp sheet) in `Android/app/src/main/kotlin/com/voiceassistant/ui/theme/Color.kt`, `Android/app/src/main/kotlin/com/voiceassistant/ui/theme/Type.kt`, `Android/app/src/main/kotlin/com/voiceassistant/ui/theme/Theme.kt`
- [ ] T030 [P] Implement iOS design tokens (light/dark color sets, Heebo font registration, Dynamic Type text styles, 20pt sheet radius) in `IOS/VoiceAssistant/UI/Theme/Theme.swift` and `IOS/VoiceAssistant/Resources/Assets.xcassets/`
- [X] T031 [P] Add automated contrast check (WCAG 2.2 AA) over the token pairs for light and dark in `Angular/src/styles/tokens.contrast.spec.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Speak a question and get an answer (Priority: P1) 🎯 MVP

**Goal**: Record audio in the web app, transcribe server-side, return a transcript and a fixed answer with a source.

**Independent Test**: Angular app against Docker Compose backend shows transcript and answer for a recorded clip.

### Tests for User Story 1 ⚠️ (write first, must FAIL)

- [X] T032 [P] [US1] Unit test `AskQuestion` with `FakeTranscriber` and `FixedAnswerGenerator` in `FastApi/tests/unit/application/test_ask_question.py`
- [X] T033 [P] [US1] Contract test suite for the `Transcriber` port in `FastApi/tests/contract/test_transcriber_contract.py`
- [X] T034 [P] [US1] Integration test `POST /v1/questions` (valid audio, empty audio → 422 Problem Details) in `FastApi/tests/integration/test_questions_api.py`
- [X] T035 [P] [US1] Component test for `voice-capture` (MediaRecorder mocked) in `Angular/src/app/voice-capture/voice-capture.component.spec.ts`
- [X] T036 [P] [US1] Playwright E2E record → answer flow in `Angular/e2e/ask-question.spec.ts`
- [X] T037 [P] [US1] Component tests: listening overlay announces status, honors reduced motion, Cancel/Done transitions in `Angular/src/app/voice-capture/listening-overlay.component.spec.ts`
- [X] T038 [P] [US1] Component tests: `code-block` copy writes to clipboard; suggestions start a question; context chip clears in `Angular/src/app/conversation/conversation.component.spec.ts`
- [X] T039 [P] [US1] Unit tests for `ShortcutsService` (Ctrl+Shift+M, Esc) in `Angular/src/app/core/shortcuts/shortcuts.service.spec.ts`

### Implementation for User Story 1

- [X] T040 [P] [US1] Define `Transcriber` port in `FastApi/app/application/ports/transcriber.py`
- [X] T041 [P] [US1] Define `AnswerGenerator` port in `FastApi/app/application/ports/answer_generator.py`
- [X] T042 [P] [US1] Implement `FakeTranscriber` and `FixedAnswerGenerator` in `FastApi/tests/fakes/`
- [X] T043 [US1] Implement `AskQuestion` use case (transcribe → answer) in `FastApi/app/application/use_cases/ask_question.py`
- [X] T044 [P] [US1] Implement `FasterWhisperTranscriber` adapter in `FastApi/app/adapters/outbound/stt/faster_whisper_transcriber.py`
- [X] T045 [P] [US1] Implement `TranscriberFactory` (config-driven) in `FastApi/app/adapters/outbound/stt/factory.py`
- [X] T046 [US1] Implement `POST /v1/questions` router, request/response schemas and audio validation (size, codec) in `FastApi/app/adapters/inbound/rest/questions.py`
- [X] T047 [US1] Wire US1 adapters in the composition root `FastApi/app/main.py`
- [X] T048 [US1] Update `FastApi/api-contracts/openapi.yaml` with `/v1/questions` and generate the TypeScript client into `Angular/src/app/core/api/`
- [X] T049 [P] [US1] Implement `AudioRecorderService` (MediaRecorder, WebM/Opus) in `Angular/src/app/voice-capture/audio-recorder.service.ts`
- [X] T050 [P] [US1] Implement `listening-overlay` dumb component per `UX/UI /angular.html` (pulsing waveform bars via AnalyserNode, "Listening…" `role=status`, "Auto-stop in N s" progress ring, Cancel and Done buttons, `prefers-reduced-motion` respected) in `Angular/src/app/voice-capture/listening-overlay.component.ts`
- [X] T051 [P] [US1] Implement `mic-button` (56px primary circle, label "Start listening, shortcut Control Shift M") and `text-input` fallback pill input in `Angular/src/app/voice-capture/mic-input.component.ts`
- [X] T052 [US1] Implement `conversation` smart component with signals state and idle / listening / answer views (state machine) in `Angular/src/app/conversation/conversation.component.ts`
- [X] T053 [P] [US1] Implement `context-chip` ("Spring · Java", clearable, 44px target, aria-label "Clear context: Spring, Java") in `Angular/src/app/conversation/context-chip.component.ts`
- [X] T054 [P] [US1] Implement `suggestion-list` ("Try asking" with 4 suggestions that start a question) in `Angular/src/app/conversation/suggestion-list.component.ts`
- [X] T055 [P] [US1] Implement `answer-card` with `code-block` (language header, Copy button with clipboard + confirmation, JetBrains Mono, syntax-token colors) in `Angular/src/app/conversation/answer-card.component.ts` and `Angular/src/app/shared/code-block.component.ts`
- [X] T056 [P] [US1] Implement `user-bubble` with Edit-question action (re-opens input with the transcript) in `Angular/src/app/conversation/user-bubble.component.ts`
- [X] T057 [US1] Implement app shell: left navigation rail (Ask, History, Saved, Settings), responsive layout (history column, main, sources column collapse below 1100px) in `Angular/src/app/core/shell/shell.component.ts` and `Angular/src/app/app.routes.ts`
- [X] T058 [P] [US1] Implement keyboard shortcuts `Ctrl+Shift+M` (start listening) and `Esc` (cancel) with on-screen hint in `Angular/src/app/core/shortcuts/shortcuts.service.ts`
- [X] T059 [P] [US1] Create Angular multi-stage Dockerfile and nginx config in `Angular/deploy/docker/Dockerfile` and `Angular/deploy/docker/nginx.conf`
- [X] T060 [US1] Add Angular service to `FastApi/deploy/docker/docker-compose.yml`

**Checkpoint**: User Story 1 works end to end via Docker Compose and is demonstrable as the MVP

---

## Phase 4: User Story 2 - Answers grounded in a knowledge base (Priority: P2)

**Goal**: Ingest Java/Spring docs into Qdrant and answer from retrieved chunks (hybrid search + rerank).

**Independent Test**: After seeding, "create a controller and service in Java" returns the expected chunks in top-k.

### Tests for User Story 2 ⚠️

- [X] T061 [P] [US2] Contract test suite for `VectorWriter`/`VectorSearcher` (sorted by score desc) run against in-memory and Qdrant in `FastApi/tests/contract/test_vector_store_contract.py`
- [X] T062 [P] [US2] Unit tests for chunking strategies (sentence, token, code-aware class/method) in `FastApi/tests/unit/application/test_chunking.py`
- [X] T063 [P] [US2] Unit test `IngestDocument` idempotency (content-hash IDs) in `FastApi/tests/unit/application/test_ingest_document.py`
- [X] T064 [P] [US2] Retrieval recall@k test over known questions in `FastApi/tests/integration/test_retrieval_recall.py`
- [X] T065 [P] [US2] Integration test Qdrant adapter with testcontainers in `FastApi/tests/integration/test_qdrant_store.py`

### Implementation for User Story 2

- [X] T066 [P] [US2] Define ports `Embedder`, `VectorWriter`, `VectorSearcher`, `Reranker` in `FastApi/app/application/ports/`
- [X] T067 [P] [US2] Implement chunking strategies (Strategy pattern) in `FastApi/app/application/services/chunking.py`
- [X] T068 [P] [US2] Implement `InMemoryVectorStore` and `FakeEmbedder` in `FastApi/tests/fakes/`
- [X] T069 [P] [US2] Implement `SentenceTransformerEmbedder` in `FastApi/app/adapters/outbound/embeddings/sentence_transformer_embedder.py`
- [X] T070 [P] [US2] Implement `CachedEmbedder` decorator (Redis) in `FastApi/app/adapters/outbound/embeddings/cached_embedder.py`
- [X] T071 [US2] Implement `QdrantVectorStore` with hybrid dense+BM25 search and payload filters (`language`, `framework`, `artifact_type`) in `FastApi/app/adapters/outbound/qdrant/qdrant_vector_store.py`
- [X] T072 [P] [US2] Implement baseline score-based `Reranker` in `FastApi/app/adapters/outbound/rerank/score_reranker.py`
- [X] T073 [US2] Implement `IngestDocument` use case and `IngestionFacade.ingest(repo_url)` in `FastApi/app/application/use_cases/ingest_document.py`
- [X] T074 [US2] Implement Celery ingestion task in `FastApi/app/workers/ingestion_tasks.py`
- [X] T075 [US2] Implement `POST /v1/ingestions` and status endpoint in `FastApi/app/adapters/inbound/rest/ingestions.py`
- [X] T076 [US2] Extend `AskQuestion` with embed → search → rerank in `FastApi/app/application/use_cases/ask_question.py`
- [X] T077 [P] [US2] Add Java/Spring seed corpus and loader script in `FastApi/ml/training/seed_corpus/` and `FastApi/scripts/seed_knowledge.py`
- [X] T078 [P] [US2] Add Qdrant collection bootstrap (`code_knowledge`) in `FastApi/app/adapters/outbound/qdrant/bootstrap.py`
- [X] T079 [US2] Update OpenAPI (sources with title, kind, origin URL) and regenerate the Angular client in `FastApi/api-contracts/openapi.yaml` and `Angular/src/app/core/api/`
- [X] T080 [P] [US2] Implement Sources column (cards: title, "Documentation · spring.io", opens in new tab) in `Angular/src/app/conversation/sources-panel.component.ts` and "Sources" chips inside the answer card in `Angular/src/app/conversation/answer-card.component.ts`
- [X] T081 [P] [US2] Component test for sources panel and source chips in `Angular/src/app/conversation/sources-panel.component.spec.ts`

**Checkpoint**: User Stories 1 and 2 both work independently

---

## Phase 5: User Story 3 - Intent and entity understanding (Priority: P3)

**Goal**: Wire the intent model into the request path (adapter, filters, fallback) and gate it in CI. Training, calibration and datasets live in US9/US10.

**Independent Test**: With a model served by TF Serving (from US10, or the baseline/fake), "make a Spring service" yields the expected intent/entities and the golden-set gate runs in CI.

### Tests for User Story 3 ⚠️

- [X] T082 [P] [US3] Contract test suite for `IntentClassifier` in `FastApi/tests/contract/test_intent_classifier_contract.py`
- [X] T083 [P] [US3] Golden-set accuracy test (threshold from env) in `FastApi/tests/ml/test_intent_golden_set.py`
- [X] T084 [P] [US3] Unit test low-confidence fallback to `FIND_DOCS` in `FastApi/tests/unit/application/test_intent_fallback.py`

### Implementation for User Story 3

- [X] T085 [P] [US3] Define `IntentClassifier` port in `FastApi/app/application/ports/intent_classifier.py`
- [X] T086 [US3] Implement `TFServingIntentClassifier` adapter (gRPC/REST) in `FastApi/app/adapters/outbound/intent/tf_serving_classifier.py`
- [X] T087 [P] [US3] Implement `FakeClassifier` in `FastApi/tests/fakes/`
- [X] T088 [US3] Wire intent into `AskQuestion` (entities → search filters, confidence fallback) in `FastApi/app/application/use_cases/ask_question.py`
- [X] T089 [P] [US3] Add TF Serving container to `FastApi/deploy/docker/docker-compose.yml` and `FastApi/deploy/docker/tf-serving.Dockerfile`
- [X] T090 [US3] Add golden-set gate job to `.github/workflows/backend.yml`

**Checkpoint**: Intent-aware retrieval works and is guarded by CI

---

## Phase 6: User Story 4 - Generated answers with graceful degradation (Priority: P4)

**Goal**: Ollama-generated answers with a circuit breaker and retrieval-only fallback.

**Independent Test**: With Ollama stopped, questions still return snippet answers.

### Tests for User Story 4 ⚠️

- [X] T091 [P] [US4] Unit tests for `CircuitBreakerGenerator` states (closed/open/half-open) in `FastApi/tests/unit/adapters/test_circuit_breaker_generator.py`
- [X] T092 [P] [US4] Unit tests for `AnswerBuilder` (text, sources, confidence, snippets) in `FastApi/tests/unit/application/test_answer_builder.py`
- [X] T093 [P] [US4] Integration test fallback when LLM is down in `FastApi/tests/integration/test_llm_fallback.py`

### Implementation for User Story 4

- [X] T094 [P] [US4] Implement `AnswerBuilder` in `FastApi/app/application/services/answer_builder.py`
- [X] T095 [P] [US4] Implement `SnippetAnswerGenerator` (retrieval-only) in `FastApi/app/adapters/outbound/answer/snippet_answer_generator.py`
- [X] T096 [P] [US4] Implement `OllamaAnswerGenerator` with RAG prompt template and timeouts in `FastApi/app/adapters/outbound/answer/ollama_answer_generator.py`
- [X] T097 [US4] Implement `CircuitBreakerGenerator` decorator with fallback in `FastApi/app/adapters/outbound/answer/circuit_breaker_generator.py`
- [X] T098 [US4] Wire generators in the composition root and add LLM settings in `FastApi/app/main.py` and `FastApi/app/config.py`
- [X] T099 [P] [US4] Add `AnswerDelivered` domain event and in-process event bus in `FastApi/app/application/events.py`

**Checkpoint**: Answers are generated with graceful degradation

---

## Phase 7: User Story 5 - Mobile clients (Priority: P5)

**Goal**: Android and iOS apps record audio and use the shared OpenAPI contract.

**Independent Test**: Each app records a question against staging and renders the answer.

### Tests for User Story 5 ⚠️

- [ ] T100 [P] [US5] Android unit tests for `AskQuestionViewModel` and `AskQuestionUseCase` (JUnit5 + MockK) in `Android/app/src/test/kotlin/com/voiceassistant/ask/`
- [ ] T101 [P] [US5] iOS unit tests for `AskQuestionViewModel` with a mocked repository protocol in `IOS/VoiceAssistantTests/AskQuestionViewModelTests.swift`
- [ ] T102 [P] [US5] Compose UI tests per `UX/UI /android.html`: idle (suggestions, context chip), listening bottom sheet with scrim and Cancel/Done, answer with code Copy, bottom navigation selection, TalkBack labels in `Android/app/src/androidTest/kotlin/com/voiceassistant/ask/AskScreenTest.kt`
- [ ] T103 [P] [US5] Android screenshot tests (light and dark, Idle/Listening/Answer) in `Android/app/src/androidTest/kotlin/com/voiceassistant/ask/AskScreenshotTest.kt`
- [ ] T104 [P] [US5] XCUITest per `UX/UI /ios.html`: large-title idle, listening sheet, answer header with context, code Copy, tab bar, VoiceOver labels in `IOS/VoiceAssistantUITests/AskQuestionUITests.swift`
- [ ] T105 [P] [US5] iOS snapshot tests (light, dark, largest Dynamic Type) for Idle/Listening/Answer in `IOS/VoiceAssistantUITests/AskSnapshotTests.swift`

### Implementation for User Story 5

- [ ] T106 [P] [US5] Generate Kotlin client from `FastApi/api-contracts/openapi.yaml` into `Android/app/src/main/kotlin/com/voiceassistant/data/api/`
- [ ] T107 [P] [US5] Generate Swift client from the OpenAPI contract into `IOS/VoiceAssistant/Data/API/`
- [ ] T108 [P] [US5] Android domain layer (`Answer`, `QuestionRepository` interface, `AskQuestionUseCase`) in `Android/app/src/main/kotlin/com/voiceassistant/domain/`
- [ ] T109 [P] [US5] iOS domain layer (`Answer`, `QuestionRepository` protocol, use case) in `IOS/VoiceAssistant/Domain/`
- [ ] T110 [US5] Android data layer (`RemoteQuestionRepository`, Retrofit/OkHttp, Keystore token storage) in `Android/app/src/main/kotlin/com/voiceassistant/data/`
- [ ] T111 [US5] iOS data layer (URLSession async/await repository, Keychain token storage) in `IOS/VoiceAssistant/Data/`
- [ ] T112 [P] [US5] Android audio capture (`AudioRecorder`, AAC/Ogg-Opus) in `Android/app/src/main/kotlin/com/voiceassistant/audio/AudioRecorder.kt`
- [ ] T113 [P] [US5] iOS audio capture (`AVAudioEngine`, M4A/AAC) in `IOS/VoiceAssistant/Audio/AudioRecorder.swift`
- [ ] T114 [US5] Android `AskQuestionViewModel` (StateFlow UI state: Idle/Listening/Answer) and Hilt module in `Android/app/src/main/kotlin/com/voiceassistant/ui/ask/AskQuestionViewModel.kt` and `Android/app/src/main/kotlin/com/voiceassistant/di/AskModule.kt`
- [ ] T115 [P] [US5] Android Ask idle screen (top app bar "Ask", context chip, "Try asking" suggestion cards 16dp, text field + 18dp mic button) in `Android/app/src/main/kotlin/com/voiceassistant/ui/ask/AskIdleContent.kt`
- [ ] T116 [P] [US5] Android `ListeningSheet` (ModalBottomSheet with grab handle, scrim, waveform, "I heard" caption, auto-stop ring, Cancel/Done) in `Android/app/src/main/kotlin/com/voiceassistant/ui/ask/ListeningSheet.kt`
- [ ] T117 [P] [US5] Android answer content (user bubble 16/4dp radius with Edit, answer card, `CodeBlock` with Copy, sources chips opening Custom Tabs) in `Android/app/src/main/kotlin/com/voiceassistant/ui/ask/AnswerContent.kt` and `Android/app/src/main/kotlin/com/voiceassistant/ui/components/CodeBlock.kt`
- [ ] T118 [US5] Android navigation: Material 3 `NavigationBar` with pill indicator (Ask, History, Saved, Settings) and NavHost in `Android/app/src/main/kotlin/com/voiceassistant/ui/navigation/AppNavigation.kt`
- [ ] T119 [US5] iOS `AskQuestionViewModel` (@Observable, Idle/Listening/Answer) in `IOS/VoiceAssistant/UI/Ask/AskQuestionViewModel.swift`
- [ ] T120 [P] [US5] iOS Ask idle view (34pt large title "Ask", context chip, suggestion cards, text field + mic button) in `IOS/VoiceAssistant/UI/Ask/AskIdleView.swift`
- [ ] T121 [P] [US5] iOS `ListeningSheet` (`.sheet` with detents, grabber, waveform, "I heard" caption, auto-stop ring, Cancel/Done) in `IOS/VoiceAssistant/UI/Ask/ListeningSheet.swift`
- [ ] T122 [P] [US5] iOS answer view (header with context caption and title, user bubble, answer card, `CodeBlockView` with Copy, sources chips via `SFSafariViewController`) in `IOS/VoiceAssistant/UI/Ask/AnswerView.swift` and `IOS/VoiceAssistant/UI/Components/CodeBlockView.swift`
- [ ] T123 [US5] iOS navigation: `TabView` (Ask, History, Saved, Settings) in `IOS/VoiceAssistant/UI/Navigation/RootTabView.swift`
- [ ] T124 [P] [US5] Android CI runner image and Fastlane lanes in `Android/deploy/docker/Dockerfile` and `Android/fastlane/Fastfile`
- [ ] T125 [P] [US5] iOS Fastlane lanes (build, test, TestFlight) in `IOS/fastlane/Fastfile`
- [ ] T126 [P] [US5] Mobile CI workflows in `.github/workflows/android.yml` and `.github/workflows/ios.yml`

**Checkpoint**: All three clients work against the same contract

---

## Phase 8: User Story 6 - Feedback and continuous learning (Priority: P6)

**Goal**: Capture and store user feedback and show feedback controls on every client. Dataset building, retraining and promotion live in US12/US13.

**Independent Test**: Submitting feedback stores it with its interaction and emits `FeedbackSubmitted`; every client shows Helpful / Not helpful.

### Tests for User Story 6 ⚠️

- [ ] T127 [P] [US6] Unit test `SubmitFeedback` emits `FeedbackSubmitted` in `FastApi/tests/unit/application/test_submit_feedback.py`
- [ ] T128 [P] [US6] Contract/integration test `FeedbackRepository` (Postgres via testcontainers) in `FastApi/tests/integration/test_feedback_repository.py`
- [ ] T129 [P] [US6] Feedback component tests in `Angular/src/app/feedback/feedback.component.spec.ts`, `Android/app/src/test/kotlin/com/voiceassistant/ui/feedback/FeedbackViewModelTest.kt`, `IOS/VoiceAssistantTests/FeedbackViewModelTests.swift`

### Implementation for User Story 6

- [ ] T130 [P] [US6] Define `FeedbackRepository` port in `FastApi/app/application/ports/feedback_repository.py`
- [ ] T131 [P] [US6] Implement `PostgresFeedbackRepository` and Alembic migration in `FastApi/app/adapters/outbound/postgres/feedback_repository.py` and `FastApi/alembic/versions/`
- [ ] T132 [US6] Implement `SubmitFeedback` use case and `POST /v1/feedback` in `FastApi/app/application/use_cases/submit_feedback.py` and `FastApi/app/adapters/inbound/rest/feedback.py`
- [ ] T133 [US6] Persist every interaction (transcript, intent, chunk IDs, answer) in `FastApi/app/adapters/outbound/postgres/interaction_repository.py`
- [ ] T134 [P] [US6] Add MLflow server to the local stack in `FastApi/deploy/docker/docker-compose.yml`
- [ ] T135 [P] [US6] Angular feedback bar ("Helpful"/"Not helpful" toggles, 44px targets, posts to `/v1/feedback`) in `Angular/src/app/feedback/feedback.component.ts`
- [ ] T136 [P] [US6] Android feedback bar (Helpful / Not helpful) in the answer card in `Android/app/src/main/kotlin/com/voiceassistant/ui/feedback/FeedbackBar.kt`
- [ ] T137 [P] [US6] iOS feedback bar (Helpful / Not helpful) in the answer view in `IOS/VoiceAssistant/UI/Feedback/FeedbackBar.swift`

**Checkpoint**: Learning loop runs end to end

---

## Phase 9: User Story 7 - Conversation experience: history, saved, settings, live captions (Priority: P7)

**Goal**: Complete the conversation UI from the design folder (`UX/UI /`): searchable history, saved answers, settings, follow-up suggestions, read-aloud/share and live "I heard" captions on web, Android and iOS.

**Independent Test**: Ask two questions, find one via History search, save it, see it under Saved, change theme in Settings, and see live captions while speaking.

### Tests for User Story 7 ⚠️

- [ ] T138 [P] [US7] Unit tests for `ListHistory` (grouping Today/Yesterday/Earlier, text search, tags such as "Spring · Java") in `FastApi/tests/unit/application/test_list_history.py`
- [ ] T139 [P] [US7] Unit tests for `SaveAnswer`/`ListSaved`/`RemoveSaved` in `FastApi/tests/unit/application/test_saved_answers.py`
- [ ] T140 [P] [US7] Integration tests for `/v1/history`, `/v1/saved`, `/v1/preferences` in `FastApi/tests/integration/test_conversation_api.py`
- [ ] T141 [P] [US7] Integration test for WebSocket `/v1/questions/stream` emitting partial transcripts then a final answer in `FastApi/tests/integration/test_questions_stream.py`
- [ ] T142 [P] [US7] Angular specs for History (search, grouping, selecting restores answer), Saved and Settings (theme, default context) in `Angular/src/app/history/history.component.spec.ts`, `Angular/src/app/saved/saved.component.spec.ts`, `Angular/src/app/settings/settings.component.spec.ts`
- [ ] T143 [P] [US7] Android ViewModel tests for history, saved and settings in `Android/app/src/test/kotlin/com/voiceassistant/ui/history/HistoryViewModelTest.kt`, `Android/app/src/test/kotlin/com/voiceassistant/ui/saved/SavedViewModelTest.kt`, `Android/app/src/test/kotlin/com/voiceassistant/ui/settings/SettingsViewModelTest.kt`
- [ ] T144 [P] [US7] iOS ViewModel tests for history, saved and settings in `IOS/VoiceAssistantTests/HistoryViewModelTests.swift`, `IOS/VoiceAssistantTests/SavedViewModelTests.swift`, `IOS/VoiceAssistantTests/SettingsViewModelTests.swift`

### Implementation for User Story 7

- [ ] T145 [P] [US7] Define ports `HistoryRepository`, `SavedAnswerRepository`, `PreferencesRepository` in `FastApi/app/application/ports/`
- [ ] T146 [US7] Implement use cases `ListHistory`, `SaveAnswer`, `ListSaved`, `RemoveSaved`, `UpdatePreferences` in `FastApi/app/application/use_cases/`
- [ ] T147 [P] [US7] Implement Postgres repositories and Alembic migration (saved_answers, preferences) in `FastApi/app/adapters/outbound/postgres/` and `FastApi/alembic/versions/`
- [ ] T148 [US7] Implement REST endpoints `/v1/history`, `/v1/saved`, `/v1/preferences` in `FastApi/app/adapters/inbound/rest/conversation.py`
- [ ] T149 [P] [US7] Add `follow_ups` (suggested next questions, e.g. "Add validation", "Write a test") to the `Answer` entity and generator output in `FastApi/app/domain/entities.py` and `FastApi/app/application/services/answer_builder.py`
- [ ] T150 [US7] Implement WebSocket `/v1/questions/stream` (partial transcripts for the "I heard" caption) and streaming method on the `Transcriber` port in `FastApi/app/adapters/inbound/rest/questions_stream.py` and `FastApi/app/application/ports/transcriber.py`
- [ ] T151 [US7] Update OpenAPI and regenerate the TypeScript, Kotlin and Swift clients in `FastApi/api-contracts/openapi.yaml`
- [ ] T152 [P] [US7] Angular History column (search field, "Today"/"Yesterday" groups, tags, current item highlighted) in `Angular/src/app/history/history.component.ts`
- [ ] T153 [P] [US7] Angular Saved page in `Angular/src/app/saved/saved.component.ts`
- [ ] T154 [P] [US7] Angular Settings page (theme Light/Dark/System, default context language and framework) in `Angular/src/app/settings/settings.component.ts`
- [ ] T155 [P] [US7] Angular answer actions Save, Share (Web Share API with clipboard fallback), Read aloud (`speechSynthesis`) in `Angular/src/app/conversation/answer-actions.component.ts`
- [ ] T156 [P] [US7] Angular follow-up chips and live "I heard" caption wired to the WebSocket stream in `Angular/src/app/conversation/follow-up-chips.component.ts` and `Angular/src/app/voice-capture/live-caption.service.ts`
- [ ] T157 [P] [US7] Android History, Saved and Settings screens (+ ViewModels, Hilt) in `Android/app/src/main/kotlin/com/voiceassistant/ui/history/`, `Android/app/src/main/kotlin/com/voiceassistant/ui/saved/`, `Android/app/src/main/kotlin/com/voiceassistant/ui/settings/`
- [ ] T158 [P] [US7] Android answer actions: Save, Share (`Intent.ACTION_SEND`), Read aloud (`TextToSpeech`), follow-up chips, live caption in `Android/app/src/main/kotlin/com/voiceassistant/ui/ask/AnswerActions.kt`
- [ ] T159 [P] [US7] iOS History, Saved and Settings views (+ ViewModels) in `IOS/VoiceAssistant/UI/History/`, `IOS/VoiceAssistant/UI/Saved/`, `IOS/VoiceAssistant/UI/Settings/`
- [ ] T160 [P] [US7] iOS answer actions: Save, Share (`ShareLink`), Read aloud (`AVSpeechSynthesizer`), follow-up chips, live caption in `IOS/VoiceAssistant/UI/Ask/AnswerActions.swift`

**Checkpoint**: Full UI parity with the design on web, Android and iOS

---

## Phase 10: User Story 8 - Production hardening (Priority: P8)

**Goal**: Kubernetes overlays, autoscaling, observability, security and Terraform for all apps.

**Independent Test**: GitOps deployment to staging passes probes; HPA scales under load; NetworkPolicies block unexpected traffic.

### Tests for User Story 7 ⚠️

- [ ] T161 [P] [US8] Manifest validation (kubeconform, kube-linter, policy checks) in `.github/workflows/infra.yml`
- [ ] T162 [P] [US8] `terraform test` suites for modules in `FastApi/deploy/terraform/tests/`
- [ ] T163 [P] [US8] Load test script verifying SC-001 latency in `FastApi/tests/load/k6_ask_question.js`

### Implementation for User Story 7

- [ ] T164 [P] [US8] Backend Kustomize base (Deployments, Services, probes, resources, securityContext, PDB) in `FastApi/deploy/k8s/base/`
- [ ] T165 [P] [US8] Backend overlays `dev`, `staging`, `prod` in `FastApi/deploy/k8s/overlays/`
- [ ] T166 [P] [US8] HPA for stateless services (STT on queue length/CPU) in `FastApi/deploy/k8s/base/hpa.yaml`
- [ ] T167 [P] [US8] StatefulSets + PVCs for Qdrant, Postgres and Redis in `FastApi/deploy/k8s/base/data/`
- [ ] T168 [P] [US8] Default-deny NetworkPolicies with explicit allows in `FastApi/deploy/k8s/base/networkpolicies.yaml`
- [ ] T169 [P] [US8] Ingress with TLS (cert-manager) and External Secrets in `FastApi/deploy/k8s/base/ingress.yaml` and `FastApi/deploy/k8s/base/externalsecrets.yaml`
- [ ] T170 [P] [US8] Observability stack (Prometheus, Grafana, Loki, OTel collector) in `FastApi/deploy/k8s/observability/`
- [ ] T171 [P] [US8] Angular K8s base + overlays (Deployment, Service, HPA, Ingress) in `Angular/deploy/k8s/`
- [ ] T172 [P] [US8] Backend Terraform (modules for cluster, networking, registry, secrets, state backend with locking) in `FastApi/deploy/terraform/`
- [ ] T173 [P] [US8] Angular Terraform (CDN/static hosting or ingress DNS) in `Angular/deploy/terraform/`
- [ ] T174 [P] [US8] Android pipeline Terraform (build runners, artifact storage, distribution) in `Android/deploy/terraform/`
- [ ] T175 [P] [US8] iOS pipeline Terraform (build runners, artifact storage, distribution) in `IOS/deploy/terraform/`
- [ ] T176 [P] [US8] Android and iOS K8s manifests for CI runners and mock-API stack in `Android/deploy/k8s/` and `IOS/deploy/k8s/`
- [ ] T177 [US8] Argo CD Applications for GitOps deployment in `FastApi/deploy/k8s/argocd/`
- [ ] T178 [US8] Add image signing (cosign), SBOM and Trivy gates to `.github/workflows/backend.yml`

**Checkpoint**: Staging deployment is hardened and observable

---

## Phase 11: User Story 9 - ML foundations: data, evaluation harness and baseline (Source: TRAINING.md phase 0) (Priority: P9)

**Goal**: Create the `FastApi/ml/` workspace, versioned and validated datasets (seed, template, paraphrased and ASR-noisy), frozen golden/challenge sets, the metric/evaluation harness, a TF-IDF baseline and the glossary corrector. Gates exist and fail red on purpose.

**Independent Test**: Run `make -C FastApi/ml data validate eval-baseline`: datasets validate, the baseline metrics file is written, and `FastApi/ml/tests/test_gates.py` fails because no model meets the gates yet.

### Tests for User Story 9 ⚠️ (write first, must FAIL)

- [X] T179 [P] [US9] Leakage test: golden/challenge utterances never appear in train (normalized text) in `FastApi/ml/tests/test_no_leakage.py`
- [X] T180 [P] [US9] Group-split test: all paraphrases and ASR variants sharing a `parent_id` land in one split; time-based split orders by week in `FastApi/ml/tests/test_splits.py`
- [X] T181 [P] [US9] Glossary tests: "j p a"→`JPA`, "rest controller"→`@RestController`, "take a rest" unchanged, neighbouring words never swallowed, overlap-free matches in `FastApi/ml/tests/test_glossary.py`
- [X] T182 [P] [US9] PII scrubber tests (API keys, emails, tokens, spoken secrets) in `FastApi/ml/tests/test_pii.py`
- [X] T183 [P] [US9] Dataset schema tests (BIO tags length equals tokens, intent in taxonomy, no empty strings, duplicate rate below limit, `source` and `parent_id` fields) in `FastApi/ml/tests/test_dataset_schema.py`
- [X] T184 [P] [US9] Metric unit tests (macro-F1, seqeval slot F1, ECE, recall@k, MRR, nDCG@5, WER, technical term error rate) in `FastApi/ml/tests/test_metrics.py`
- [X] T185 [P] [US9] Gate tests (floors: intent macro-F1 0.90, slot F1 0.85, OOD recall 0.90, ECE 0.05, recall@5 0.85, no slice regresses > 0.01 vs champion) written to FAIL initially in `FastApi/ml/tests/test_gates.py`

### Implementation for User Story 9

- [X] T186 [US9] Create the ML workspace tree `FastApi/ml/{data/{raw,interim,processed,golden},glossary,prompts,training/{intent,embedder,reranker,common},evaluation,pipelines,registry,tests}` with `__init__.py` files and a `FastApi/ml/Makefile` (targets `data`, `validate`, `eval-baseline`, `test`)
- [X] T187 [US9] Add the `ml` dependency group (TensorFlow, Keras 3, keras-hub, scikit-learn, scipy, seqeval, jiwer, mlflow, dvc, great-expectations, rapidfuzz, piper-tts, label-studio-sdk), latest stable pinned at scaffold time, to `FastApi/pyproject.toml`
- [X] T188 [P] [US9] Initialize DVC with a MinIO remote and track `FastApi/ml/data/` in `FastApi/ml/.dvc/config` and `FastApi/ml/data/.gitignore`
- [X] T189 [P] [US9] Define the intent taxonomy (8 mutually exclusive intents incl. `OUT_OF_SCOPE`, each mapped to one handler) and the entity schema (`LANGUAGE`, `FRAMEWORK`, `ARTIFACT`, `LIBRARY`, `VERSION`, `ERROR_CODE`, BIO tagging) in `FastApi/ml/data/taxonomy.yaml`
- [X] T190 [P] [US9] Write labeling guidelines (5–10 examples per intent and boundary case, hard-negative rules for "controller") in `FastApi/ml/docs/labeling-guidelines.md`
- [X] T191 [P] [US9] Create the hand-written seed set (50–100 utterances per intent incl. typos, fragments, `OUT_OF_SCOPE` hard negatives) in `FastApi/ml/data/raw/seed.jsonl`
- [X] T192 [P] [US9] Implement template expansion (slots × phrasings) with a per-intent cap on synthetic share in `FastApi/ml/training/common/template_expansion.py`
- [X] T193 [P] [US9] Implement LLM paraphrasing via Ollama with a 10–20% human-review sample export (Label Studio JSON) and synthetic-share tracking in `FastApi/ml/training/common/paraphrase.py`
- [X] T194 [P] [US9] Implement ASR-in-the-loop augmentation (Piper TTS voices and speed, background noise SNR 5–30 dB, re-encode WebM/Opus and AAC with ffmpeg, transcribe with faster-whisper, copy gold labels, keep `parent_id`) in `FastApi/ml/training/common/asr_augment.py`
- [X] T195 [P] [US9] Implement JSONL readers/writers and `tf.data` builders (tokenization, `cache()`, `prefetch()`) in `FastApi/ml/training/common/datasets.py`
- [X] T196 [P] [US9] Implement group-based and time-based splitters in `FastApi/ml/training/common/splits.py`
- [X] T197 [P] [US9] Implement the PII/secret scrubber in `FastApi/ml/training/common/pii.py`
- [X] T198 [P] [US9] Implement metrics (macro-F1, entity F1 via seqeval, ECE, recall@k, MRR@10, nDCG@5, WER via jiwer, TTER) in `FastApi/ml/training/common/metrics.py`
- [X] T199 [P] [US9] Implement annotator agreement (Cohen kappa target ≥ 0.8) and embedding-similarity near-duplicate removal in `FastApi/ml/training/common/agreement.py` and `FastApi/ml/training/common/dedupe.py`
- [X] T200 [P] [US9] Write and freeze the 200-utterance golden set and the noisy/accented/out-of-scope challenge set, with a CI check that they are read-only, in `FastApi/ml/data/golden/golden.jsonl` and `FastApi/ml/data/golden/challenge.jsonl`
- [X] T201 [P] [US9] Add Great Expectations suites (schema, label distribution, empties, duplicate rate, leakage) in `FastApi/ml/evaluation/expectations/`
- [X] T202 [P] [US9] Implement the evaluation harness with slice reports (language, framework, audio noise level, utterance length, new vs returning users) in `FastApi/ml/evaluation/run_eval.py`
- [X] T203 [P] [US9] Implement the TF-IDF + logistic-regression baseline and record its metrics in `FastApi/ml/training/intent/baseline.py` and `FastApi/ml/evaluation/baseline_metrics.json`
- [X] T204 [P] [US9] Implement the curated glossary (canonical spellings, aliases, phonetic hints) in `FastApi/ml/glossary/terms.yaml`
- [X] T205 [US9] Implement `GlossaryCorrectedTranscriber` decorator (best-score-first, non-overlapping fuzzy matching with rapidfuzz) in `FastApi/app/adapters/outbound/stt/glossary_corrected_transcriber.py`, wired in `FastApi/app/main.py`
- [X] T206 [P] [US9] Create the ML CI workflow (data validation, ML tests, gates reported red on purpose until US10) in `.github/workflows/ml.yml`

**Checkpoint**: Datasets, harness and baseline exist; gates are measurable

---

## Phase 12: User Story 10 - Intent and slots model v1 with calibration and abstention (Source: TRAINING.md phase 1) (Priority: P10)

**Goal**: Train a joint Keras BiLSTM (intent + slots), calibrate it, handle `OUT_OF_SCOPE`, export a versioned SavedModel, register it with full reproducibility metadata and use it in the request path through the confidence gate.

**Independent Test**: Run `make -C FastApi/ml train-intent`: macro-F1 ≥ 0.90, slot F1 ≥ 0.85, OOD recall ≥ 0.90 and ECE ≤ 0.05 on the golden and challenge sets, and TF Serving serves the new version; "how do I create a controller" with no language returns `clarify`.

### Tests for User Story 10 ⚠️ (write first, must FAIL)

- [X] T207 [P] [US10] Model tests: joint model outputs `intent` and `slots` logits (linear outputs, masked padding) in `FastApi/ml/tests/test_intent_model.py`
- [X] T208 [P] [US10] Calibration tests: `fit_temperature` lowers ECE on held-out logits and is fitted only on validation data in `FastApi/ml/tests/test_calibration.py`
- [X] T209 [P] [US10] OOD tests: `OUT_OF_SCOPE` hard negatives ("how do I use a game controller") are rejected via class, calibrated threshold and retrieval-score threshold in `FastApi/ml/tests/test_out_of_scope.py`
- [X] T210 [P] [US10] Export tests: SavedModel exported to a numbered version directory with serving signature and temperature file in `FastApi/ml/tests/test_export.py`
- [X] T211 [P] [US10] Registry tests: registration is refused when git SHA, image digest, dataset hash, seeds, hyperparameters or metrics are missing in `FastApi/ml/tests/test_registry.py`
- [X] T212 [P] [US10] Unit tests for `ConfidenceGate` (answer / clarify / abstain, missing required `LANGUAGE`, `OUT_OF_SCOPE`) in `FastApi/tests/unit/domain/test_confidence_gate.py`
- [X] T213 [P] [US10] Unit tests for `IntentRouter` (handler registry, fallback, no retrieval for `META_COMMAND`) in `FastApi/tests/unit/application/test_intent_router.py`
- [X] T214 [P] [US10] Latency test: intent inference stays inside its CI budget in `FastApi/ml/tests/test_intent_latency.py`
- [X] T215 [P] [US10] Replace the placeholder golden-set test with real gate evaluation against `FastApi/ml/data/golden/` in `FastApi/tests/ml/test_intent_golden_set.py`

### Implementation for User Story 10

- [X] T216 [US10] Implement `build_joint_model` (BiLSTM, two linear-logit heads) in `FastApi/ml/training/intent/model.py`
- [X] T217 [US10] Implement training (class weights, loss weights 1.0/0.5, EarlyStopping, per-epoch checkpoints, fixed seeds, optional `mixed_float16`, MLflow logging) in `FastApi/ml/training/intent/train.py`
- [X] T218 [P] [US10] Implement temperature-scaling calibration (`fit_temperature`) in `FastApi/ml/training/intent/calibrate.py`
- [X] T219 [P] [US10] Implement intent/slot evaluation (macro-F1, slot F1, OOD recall, ECE, slices) writing `metrics.json` in `FastApi/ml/evaluation/intent_eval.py`
- [X] T220 [P] [US10] Implement SavedModel export to `artifacts/intent/<version>/` with `temperature.json` in `FastApi/ml/training/intent/export.py`
- [X] T221 [P] [US10] Implement model registration to the MLflow Registry with run metadata and model card generation in `FastApi/ml/registry/register.py` and `FastApi/ml/registry/model_card.md`
- [X] T222 [P] [US10] Create the training container image (CPU default, GPU build arg) in `FastApi/deploy/docker/ml-train.Dockerfile`
- [X] T223 [P] [US10] Configure TF Serving multi-version model config (candidate and champion side by side) in `FastApi/deploy/docker/tf-serving/models.config`
- [X] T224 [US10] Update `TFServingIntentClassifier` to apply the stored temperature and decode BIO tags into entities in `FastApi/app/adapters/outbound/intent/tf_serving_classifier.py`
- [X] T225 [US10] Implement `ConfidenceGate` policy (calibrated thresholds 0.80 / 0.50, required entities per intent) in the domain in `FastApi/app/domain/confidence_gate.py`
- [X] T226 [US10] Implement `IntentRouter` with handler registry and fallback in `FastApi/app/application/services/intent_router.py`
- [X] T227 [US10] Apply profile default entities before the gate and return `status=clarify` with option chips or `status=abstain` in `FastApi/app/application/use_cases/ask_question.py`
- [X] T228 [P] [US10] Update OpenAPI for `clarify`/`abstain` response variants and regenerate clients in `FastApi/api-contracts/openapi.yaml`
- [X] T229 [P] [US10] Add the intent metric gates (macro-F1, slot F1, OOD recall, ECE, slice regression) to `.github/workflows/ml.yml`

**Checkpoint**: Intent v1 is green on all gates and used in the request path

---

## Phase 13: User Story 11 - Retrieval quality, grounded answers and guardrails (Source: TRAINING.md phases 2–3, patterns P4–P14) (Priority: P11)

**Goal**: Improve and measure retrieval (hybrid + fusion + rerank, entity filters, versioned index), enforce grounded and safe generation (prompt-as-code, guardrails, verification, degradation ladder, semantic cache, bounded tools) and measure STT quality.

**Independent Test**: Retrieval golden set reaches recall@5 ≥ 0.85; answers cite existing sources and are ≥ 95% grounded with ≥ 95% compiling code; a chaos test that stops Ollama yields a level-1 answer inside the latency budget.

### Tests for User Story 11 ⚠️ (write first, must FAIL)

- [ ] T230 [P] [US11] Unit tests for `reciprocal_rank_fusion` in `FastApi/tests/unit/domain/test_rank_fusion.py`
- [ ] T231 [P] [US11] Unit tests for `QueryRewriter` ("now add validation" → standalone query; rule-based and fake-LLM adapters; both versions traced) in `FastApi/tests/unit/application/test_query_rewriter.py`
- [ ] T232 [P] [US11] Unit tests for hard vs soft entity filters and step-wise relaxation in `FastApi/tests/unit/application/test_entity_filters.py`
- [ ] T233 [P] [US11] Contract tests for versioned index (alias switch, rollback, query refused on embedder-version mismatch) in `FastApi/tests/contract/test_versioned_index.py`
- [ ] T234 [P] [US11] Unit tests for `SemanticCache` (key includes index version, prompt version and filters; no caching of low-confidence, personalized or unverified answers; TTL) in `FastApi/tests/unit/adapters/test_semantic_cache.py`
- [ ] T235 [P] [US11] Snapshot test of the rendered prompt with a fake LLM and schema validation in `FastApi/ml/tests/test_prompts.py`
- [ ] T236 [P] [US11] Unit tests for guardrails (schema, citation ids exist, injection-like text stripped from context, risky-command warning, blocked → safe fallback) in `FastApi/tests/unit/adapters/test_guardrails.py`
- [ ] T237 [P] [US11] Unit tests for `VerifiedGenerator` (retry once with error hint, then "not verified" note) in `FastApi/tests/unit/adapters/test_verified_generator.py`
- [ ] T238 [P] [US11] Unit tests for the degradation ladder levels 0–3 and a chaos integration test (Ollama stopped → level 1 within budget) in `FastApi/tests/integration/test_degradation_ladder.py`
- [ ] T239 [P] [US11] Unit tests for `ToolRegistry` (allowlist, JSON-schema args, max calls, side-effect confirmation) in `FastApi/tests/unit/application/test_tool_registry.py`
- [ ] T240 [P] [US11] Retrieval golden-set evaluation test (recall@5, MRR@10) in `FastApi/ml/tests/test_retrieval_gates.py`
- [ ] T241 [P] [US11] STT evaluation test (WER ≤ 10% clean, TTER ≤ 5%) over recorded samples in `FastApi/ml/tests/test_stt_gates.py`
- [ ] T242 [P] [US11] Answer evaluation test (groundedness ≥ 95%, code validity ≥ 95%) in `FastApi/ml/tests/test_answer_gates.py`

### Implementation for User Story 11

- [ ] T243 [US11] Implement RRF fusion in `FastApi/app/domain/rank_fusion.py`
- [ ] T244 [US11] Implement two-stage retriever (dense top 50 + BM25 top 50 → RRF keep 20 → rerank to 5) in `FastApi/app/application/services/two_stage_retriever.py`
- [ ] T245 [P] [US11] Implement entity-to-filter mapping (hard: language; ranking features: framework, version) with relaxation notices in `FastApi/app/application/services/entity_filters.py`
- [ ] T246 [P] [US11] Define `QueryRewriter` port and rule-based and LLM adapters in `FastApi/app/application/ports/query_rewriter.py` and `FastApi/app/adapters/outbound/rewrite/`
- [ ] T247 [US11] Implement versioned collections (`code_knowledge_vN`), alias switch/rollback and `embedder_version` guard in `FastApi/app/adapters/outbound/qdrant/versioned_index.py` and CLI `FastApi/scripts/index_admin.py` — owned by US31: use `T591` and `T592`; do not duplicate
- [ ] T248 [P] [US11] Implement `SemanticCache` decorator (Redis vector search, threshold 0.95 tunable) in `FastApi/app/adapters/outbound/cache/semantic_cache.py` — vector lookup uses the Qdrant `semantic_cache` collection from US32 (T609), not Redis vector search
- [ ] T249 [P] [US11] Define `PromptRepository` port and YAML prompt loader in `FastApi/app/application/ports/prompt_repository.py` and `FastApi/app/adapters/outbound/prompts/yaml_prompt_repository.py`
- [ ] T250 [P] [US11] Write the versioned prompt `answer_with_citations` v7 and `answer.schema.json` (steps, code, cite, sources) in `FastApi/ml/prompts/answer_with_citations.v7.yaml` and `FastApi/ml/prompts/answer.schema.json`
- [ ] T251 [US11] Implement grounded generation (numbered sources, schema-validated output, citation existence check, abstain below score threshold) in `FastApi/app/adapters/outbound/answer/grounded_answer_generator.py`
- [ ] T252 [P] [US11] Implement `GuardrailPipeline` and guards (`SchemaGuard`, `CitationGuard`, `InputSecretGuard`, `RetrievedContentGuard`, `RiskyCommandGuard`) in `FastApi/app/adapters/outbound/guardrails/`
- [ ] T253 [P] [US11] Define `CodeVerifier` port and `SyntaxOnlyVerifier` fallback in `FastApi/app/application/ports/code_verifier.py` and `FastApi/app/adapters/outbound/verify/syntax_verifier.py`
- [ ] T254 [P] [US11] Implement `JavaCompileVerifier` in an isolated sandbox (no network, CPU/memory/time limits, throwaway filesystem) in `FastApi/app/adapters/outbound/verify/java_compile_verifier.py` and `FastApi/deploy/docker/sandbox.Dockerfile`
- [ ] T255 [P] [US11] Implement `VerifiedGenerator` decorator in `FastApi/app/adapters/outbound/answer/verified_generator.py`
- [ ] T256 [US11] Implement the degradation ladder (0 full → 1 extractive snippets → 2 keyword/doc links → 3 retry message) and wire the decorator stack in `FastApi/app/adapters/outbound/answer/degradation_ladder.py` and `FastApi/app/main.py`
- [ ] T257 [P] [US11] Implement `ToolRegistry` and the fixed `CREATE_CODE_ARTIFACT` workflow (`search_docs` → `get_template` → `fill_template` → `verify_code`) in `FastApi/app/application/services/tool_registry.py` and `FastApi/app/application/workflows/create_code_artifact.py`
- [ ] T258 [P] [US11] Add Whisper `initial_prompt`/`hotwords` and VAD settings from the glossary to `FastApi/app/adapters/outbound/stt/faster_whisper_transcriber.py`
- [ ] T259 [P] [US11] Create the retrieval golden set (known questions → expected chunk ids) in `FastApi/ml/data/golden/retrieval.jsonl` and the recorded-audio STT set manifest in `FastApi/ml/data/golden/stt_manifest.jsonl`
- [ ] T260 [P] [US11] Implement retrieval, STT and answer evaluation scripts (LLM-as-judge from a different model, calibrated against human labels) in `FastApi/ml/evaluation/retrieval_eval.py`, `FastApi/ml/evaluation/stt_eval.py`, `FastApi/ml/evaluation/answer_eval.py`
- [ ] T261 [P] [US11] Add retrieval, STT and answer gates and the chaos test to `.github/workflows/ml.yml`

**Checkpoint**: Retrieval and generation meet their gates with safe degradation

---

## Phase 14: User Story 12 - Feedback capture, decision traces and review queue (Source: TRAINING.md phase 4, patterns P15, P18) (Priority: P12)

**Goal**: Record a replayable decision trace per request, capture consented, structured feedback and transcript edits, turn them into candidate training examples with filters, and prioritize human review with active learning. No retraining yet.

**Independent Test**: Ask a question, submit thumbs-down with reason `wrong_language`: one trace exists with all stage versions, a hard-negative candidate and a slot-review item appear in the review queue, and replaying the trace reproduces the same decisions.

### Tests for User Story 12 ⚠️ (write first, must FAIL)

- [ ] T262 [P] [US12] Unit tests for `DecisionTrace` capture across stages (input, output, score, latency, model/index/prompt versions, hashed user id) in `FastApi/tests/unit/application/test_decision_trace.py`
- [ ] T263 [P] [US12] Schema tests for the `feedback.submitted` event (vote, reason enum, `consent_training`, model_versions, index_version, chunk_ids) in `FastApi/tests/unit/domain/test_feedback_event.py`
- [ ] T264 [P] [US12] Unit tests for signal mapping (thumbs up + code copy = strong positive; wrong_language = hard negative; edit = gold correction; re-ask = review only; no action is never negative) in `FastApi/tests/unit/application/test_signal_mapper.py`
- [ ] T265 [P] [US12] Unit tests for candidate filters (consent flag, PII scrub, dedupe, agreement rule) in `FastApi/tests/unit/application/test_candidate_builder.py`
- [ ] T266 [P] [US12] Unit tests for active-learning sampler (margin < 0.15, champion/challenger disagreement, cluster diversity) in `FastApi/ml/tests/test_active_learning.py`
- [ ] T267 [P] [US12] Integration tests for review queue API and deletion propagation to derived datasets in `FastApi/tests/integration/test_review_queue.py`
- [ ] T268 [P] [US12] Replay test: stored traces re-run against a candidate and compared on intent, gate and final chunk ids in `FastApi/ml/tests/test_replay.py`
- [ ] T269 [P] [US12] Unit tests for drift metrics (OOD rate, mean calibrated confidence, top-1 retrieval score distribution, thumbs-down rate) in `FastApi/ml/tests/test_drift_metrics.py`

### Implementation for User Story 12

- [ ] T270 [US12] Implement `DecisionTrace` entity, Postgres table and Alembic migration in `FastApi/app/domain/decision_trace.py` and `FastApi/app/adapters/outbound/postgres/trace_repository.py`
- [ ] T271 [US12] Implement tracing decorators (`TracingTranscriber`, `TracingIntentClassifier`, `TracingRetriever`, `TracingGenerator`) emitting OpenTelemetry spans and trace rows in `FastApi/app/adapters/outbound/tracing/`
- [ ] T272 [P] [US12] Extend `POST /v1/feedback` to the full event schema with reason enum and `consent_training` in `FastApi/app/adapters/inbound/rest/feedback.py`
- [ ] T273 [P] [US12] Implement `PATCH /v1/questions/{id}/transcript` storing gold ASR corrections as glossary candidates in `FastApi/app/adapters/inbound/rest/transcript_edit.py`
- [ ] T274 [P] [US12] Implement Celery task `process_feedback` (stores the event with its trace; rate limits and per-user caps) in `FastApi/app/workers/feedback_tasks.py`
- [ ] T275 [P] [US12] Implement the signal-to-candidate mapper in `FastApi/app/application/services/signal_mapper.py`
- [ ] T276 [P] [US12] Implement nightly `build_candidates` task (consent, PII scrub, dedupe, agreement rules) in `FastApi/app/workers/candidate_tasks.py`
- [ ] T277 [P] [US12] Implement review queue entity, Postgres storage and endpoints (list, confirm, fix, reject) in `FastApi/app/application/use_cases/review_queue.py` and `FastApi/app/adapters/inbound/rest/review.py`
- [ ] T278 [P] [US12] Implement the active-learning prioritizer in `FastApi/ml/training/common/active_learning.py` and export to Label Studio in `FastApi/ml/pipelines/export_review_batch.py`
- [ ] T279 [P] [US12] Implement consent-aware deletion propagation across derived datasets and audio retention expiry job in `FastApi/app/workers/privacy_tasks.py`
- [ ] T280 [P] [US12] Implement the trace replay CLI in `FastApi/ml/evaluation/replay.py`
- [ ] T281 [P] [US12] Add Prometheus metrics (helpful rate, copy-code rate, transcript edit rate, reformulation rate, abstain rate, OOD rate, confidence, top-1 score) in `FastApi/app/adapters/outbound/tracing/metrics.py`
- [ ] T282 [P] [US12] Add Grafana dashboards for online quality and drift in `FastApi/deploy/k8s/observability/dashboards/ml-quality.json`

**Checkpoint**: Feedback and traces are captured, replayable and reviewable

---

## Phase 15: User Story 13 - Learning loop v1: embedder and reranker training, automation and champion/challenger (Source: TRAINING.md phases 5–6, patterns P16–P17) (Priority: P13)

**Goal**: Fine-tune the embedder (contrastive, hard negatives) and train the reranker (listwise, position-bias aware) from reviewed data, orchestrate dataset build → training Job → evaluation → human approval with Celery and Kubernetes, and promote models through shadow, canary and alias promotion with one-step rollback.

**Independent Test**: A scheduled run builds dataset N+1, trains on a Kubernetes Job, evaluates against the champion, and registers a candidate; the candidate runs in shadow, passes gates, gets promoted by alias after human approval and can be rolled back with one command.

### Tests for User Story 13 ⚠️ (write first, must FAIL)

- [ ] T283 [P] [US13] Unit tests for `info_nce` loss (diagonal positives, `[B, B+H]` logits with hard negatives, in-batch dedupe by `positive_chunk_id`) in `FastApi/ml/tests/test_info_nce.py`
- [ ] T284 [P] [US13] Unit tests for hard-negative mining (thumbs-down `wrong_language`, near-miss wrong framework) in `FastApi/ml/tests/test_hard_negatives.py`
- [ ] T285 [P] [US13] Unit tests for reranker listwise loss, graded labels (unlabeled ≠ negative) and inverse-propensity weights from `shown_pos` in `FastApi/ml/tests/test_reranker_training.py`
- [ ] T286 [P] [US13] Contract tests for `Embedder` and `Reranker` adapters (sorted by score, stable ids, versions reported, refuse mismatch) in `FastApi/tests/contract/test_embedder_reranker_contract.py`
- [ ] T287 [P] [US13] Latency test: reranking 20 candidates stays within 100 ms on CPU in `FastApi/ml/tests/test_reranker_latency.py`
- [ ] T288 [P] [US13] Gate tests: candidate meets floors and no slice regresses more than 0.01 vs champion; embedder fine-tune must beat the off-the-shelf baseline on the retrieval golden set in `FastApi/ml/tests/test_promotion_gates.py`
- [ ] T289 [P] [US13] Unit tests for replay-mix dataset building (new data + old sample + golden set, never only the latest week) in `FastApi/ml/tests/test_replay_mix.py`
- [ ] T290 [P] [US13] Unit tests for champion/challenger routing (off / shadow / canary percent), shadow comparison logging and alias rollback in `FastApi/tests/unit/adapters/test_champion_challenger.py`
- [ ] T291 [P] [US13] Unit tests for retrain triggers (enough verified examples, drift alarm) and cadence config in `FastApi/ml/tests/test_retrain_triggers.py`
- [ ] T292 [P] [US13] Integration test for the Celery chain `build_dataset → launch_training_job → evaluate → notify` with a fake Kubernetes client in `FastApi/tests/integration/test_training_pipeline.py`

### Implementation for User Story 13

- [ ] T293 [US13] Implement the contrastive embedder model and `info_nce` loss in `FastApi/ml/training/embedder/model.py` and `FastApi/ml/training/embedder/losses.py`
- [ ] T294 [US13] Implement embedder training (AdamW 1e-5–2e-5, large batches, temperature 0.05, 1–3 hard negatives, MLflow logging) in `FastApi/ml/training/embedder/train.py`
- [ ] T295 [P] [US13] Implement hard-negative mining in `FastApi/ml/training/embedder/hard_negatives.py`
- [ ] T296 [US13] Implement the cross-encoder reranker with listwise softmax loss and IPW sample weights in `FastApi/ml/training/reranker/model.py` and `FastApi/ml/training/reranker/train.py`
- [ ] T297 [P] [US13] Implement the exploration slice (5% of queries shuffle the top 5) in `FastApi/app/application/services/exploration.py`
- [ ] T298 [P] [US13] Implement TF-based `Embedder` and `Reranker` adapters served via TF Serving in `FastApi/app/adapters/outbound/embeddings/tf_embedder.py` and `FastApi/app/adapters/outbound/rerank/tf_reranker.py`
- [ ] T299 [P] [US13] Implement the re-embed job that builds a new versioned index and evaluates it before the alias switch in `FastApi/ml/pipelines/reembed.py`
- [ ] T300 [P] [US13] Implement dataset versioning with DVC (dataset N+1 hash recorded in every model run) in `FastApi/ml/pipelines/build_dataset.py`
- [ ] T301 [P] [US13] Implement replay-mix dataset construction in `FastApi/ml/training/common/replay_mix.py`
- [ ] T302 [P] [US13] Implement Celery tasks `build_dataset`, `launch_training_job` (creates a Kubernetes `Job`), `evaluate`, `notify_reviewers` in `FastApi/ml/pipelines/celery_tasks.py`
- [ ] T303 [P] [US13] Create Kubernetes training `Job` templates for a GPU node pool in `FastApi/deploy/k8s/base/ml-train-job.yaml`
- [ ] T304 [P] [US13] Implement promotion service (gates, slice regression, helpful-rate delta, human approval step) in `FastApi/ml/pipelines/promote.py`
- [ ] T305 [US13] Implement champion/challenger model-serving proxy (modes off/shadow/canary, shadow decision logging) in `FastApi/app/adapters/outbound/models/champion_challenger.py`
- [ ] T306 [P] [US13] Create champion/challenger config (`champion`, `challenger`, `mode`, `canary_percent`, `promote_if`) in `FastApi/deploy/k8s/base/model-routing.yaml`
- [ ] T307 [P] [US13] Implement alias promote and one-line rollback CLI over MLflow aliases in `FastApi/ml/pipelines/alias_admin.py`
- [ ] T308 [P] [US13] Implement retrain triggers and cadence (intent weekly/biweekly, reranker biweekly, embedder monthly–quarterly, knowledge nightly) with Celery beat in `FastApi/ml/pipelines/schedule.py`
- [ ] T309 [P] [US13] Add drift alarm rules (OOD rate, confidence, top-1 score, thumbs-down rate) in `FastApi/deploy/k8s/observability/alerts/ml-drift.yaml`
- [ ] T310 [P] [US13] Add the training pipeline stages and gates to `.github/workflows/ml.yml`

**Checkpoint**: Models improve through a gated, reversible, mostly automated loop

---

## Phase 16: User Story 14 - Optional advanced models (Source: TRAINING.md phase 7, section 4) (Priority: P14)

**Goal**: Only if a measured gap justifies the cost: pretrained-encoder intent model, STT fine-tuning, LLM LoRA, and an on-device TFLite intent fallback.

**Independent Test**: Each item ships only after its trigger test shows the documented gap and its candidate beats the champion on the gates.

### Tests for User Story 14 ⚠️ (write first, must FAIL)

- [ ] T311 [P] [US14] Trigger tests (encoder: BiLSTM plateau on challenge set; STT: TTER above gate after tiers 1–3; LLM: < 90% format compliance after 3 prompt revisions) in `FastApi/ml/tests/test_optional_triggers.py`
- [ ] T312 [P] [US14] TFLite parity test (intent agreement ≥ 99% with the SavedModel on the golden set) in `FastApi/ml/tests/test_tflite_parity.py`

### Implementation for User Story 14

- [ ] T313 [P] [US14] Fine-tune a small pretrained encoder with KerasHub (`TextClassifier` + token-level head for slots, AdamW 2e-5, warmup ~10%) using the pinned preset in `FastApi/ml/training/intent/encoder_train.py`
- [ ] T314 [P] [US14] Build the separate PyTorch/HF Whisper fine-tune pipeline with CTranslate2 conversion for faster-whisper in `FastApi/ml/training/stt/finetune.py` and `FastApi/ml/training/stt/convert.py`
- [ ] T315 [P] [US14] Build the separate LoRA/QLoRA pipeline on curated (question, context, answer) triples, never on unverified model output, in `FastApi/ml/training/llm/lora.py`
- [ ] T316 [P] [US14] Export the intent model to TFLite for the mobile offline fallback in `FastApi/ml/training/intent/export_tflite.py`

**Checkpoint**: Optional capabilities available behind measured gates

---

## Phase 17: User Story 15 - Postman collections for the backend endpoints (Priority: P15)

**Goal**: Generate a versioned Postman collection (v2.1) and environments from the OpenAPI contract, with auth, test scripts, realistic flows and negative scenarios, runnable in Postman and in CI with Newman.

**Independent Test**: `make postman-check && make newman` passes against a locally started API (fake STT engine); importing the collection in Postman and selecting the `local` environment lets a developer call every endpoint with one click.

### Tests for User Story 15 ⚠️ (write first, must FAIL)

- [X] T317 [P] [US15] Generator unit tests: one folder per OpenAPI tag, one request per operation, `{{baseUrl}}` host, bearer `{{accessToken}}` only on secured operations, multipart `audio` file field, `{{jobId}}` path variable and saved example responses (incl. `application/problem+json`) in `FastApi/tests/unit/test_postman_generator.py`
- [X] T318 [P] [US15] Test-script tests: every generated request carries assertions for status code, content type, response schema, `X-Correlation-ID` and a latency budget in `FastApi/tests/unit/test_postman_test_scripts.py`
- [X] T319 [P] [US15] Coverage and drift test: every operation in `FastApi/api-contracts/openapi.yaml` is present in the committed collection, and regenerating produces byte-identical JSON in `FastApi/tests/contract/test_postman_collection.py`
- [X] T320 [P] [US15] Hygiene test: valid Postman v2.1 structure, no literal tokens, passwords or hostnames outside variables, and environment secrets typed `secret` with empty values in `FastApi/tests/contract/test_postman_hygiene.py`
- [X] T321 [P] [US15] Unit tests for the `fake` STT engine (deterministic transcript for any non-empty audio, rejects empty audio, refuses to start when `environment` is `production`) in `FastApi/tests/unit/test_fake_transcriber.py`
- [X] T322 [P] [US15] Newman smoke test: run the collection against a live uvicorn with the fake STT engine and assert zero failures (skipped when `newman` is missing) in `FastApi/tests/integration/test_newman_smoke.py`

### Implementation for User Story 15

- [X] T323 [US15] Implement the `fake` STT engine (CI, local and Postman use only) and register it in `TranscriberFactory` in `FastApi/app/adapters/outbound/stt/fake_transcriber.py` and `FastApi/app/adapters/outbound/stt/factory.py`
- [X] T324 [US15] Implement the OpenAPI 3.1 → Postman Collection v2.1 generator (folders by tag, variables, auth, example bodies, saved examples, deterministic ordering) in `FastApi/scripts/postman_collection.py`
- [X] T325 [P] [US15] Write the shared test snippets (status, problem+json shape, JSON-schema validation of the response, correlation id, latency budget) injected into every request by the generator in `FastApi/postman/scripts/tests.js`
- [X] T326 [P] [US15] Write the collection pre-request script (Keycloak token via password or client-credentials grant with expiry caching, `X-Correlation-ID` generation) in `FastApi/postman/scripts/pre-request.js`
- [X] T327 [P] [US15] Create environments `local`, `docker-compose` and `staging` with `baseUrl`, `keycloakUrl`, `realm`, `clientId`, and secret-typed `username`, `password`, `accessToken` (empty values) in `FastApi/postman/environments/`
- [X] T328 [P] [US15] Add audio fixtures and a script to regenerate them (`ffmpeg` sine-tone WebM/Opus and AAC clips, plus a minimal EBML file for the fake STT) in `FastApi/postman/fixtures/` and `FastApi/scripts/make_audio_fixtures.sh`
- [X] T329 [P] [US15] Author the flow definitions the generator merges into the collection: ask a question (happy path) in `FastApi/postman/flows/ask_question.yaml`
- [X] T330 [P] [US15] Author the ingestion flow: submit a seed-corpus URL, poll `/v1/ingestions/{{jobId}}` until `succeeded` with `postman.setNextRequest`, then ask a question and assert sources in `FastApi/postman/flows/ingest_then_ask.yaml`
- [X] T331 [P] [US15] Author the negative scenarios (401 missing token, 403 missing `ingest` role, 404 unknown job, 413 oversized audio, 415 wrong type, 422 empty audio and blank URL) in `FastApi/postman/flows/negative.yaml`
- [X] T332 [P] [US15] Author the health and smoke folder (`/health/live`, `/health/ready`) that runs first in `FastApi/postman/flows/health.yaml`
- [X] T333 [US15] Generate and commit the collection with `python scripts/postman_collection.py` into `FastApi/postman/voice-assistant.postman_collection.json`
- [X] T334 [P] [US15] Add `make postman` (regenerate), `make postman-check` (drift test) and `make newman` (`npx newman run … -e local`) in `FastApi/Makefile`
- [X] T335 [P] [US15] Extend the Keycloak dev realm with a `dev-user` and a `dev-ingester` (role `ingest`) whose passwords come from environment variables, and a `voice-postman` client allowing the password grant in dev only, in `FastApi/deploy/docker/keycloak/realm.json`
- [X] T336 [US15] Create the Newman CI workflow: unit and drift tests on every PR, the smoke run against uvicorn with the fake STT engine and auth disabled, and a nightly full run against the compose stack with Keycloak in `.github/workflows/postman.yml`
- [X] T337 [P] [US15] Add a Prism mock server from the OpenAPI file for client development (Angular, Android, iOS) in `FastApi/deploy/docker/docker-compose.mock.yml`
- [X] T338 [P] [US15] Add an optional publisher that upserts the collection and environments to a Postman workspace using the `POSTMAN_API_KEY` secret (manual dispatch only) in `FastApi/scripts/postman_sync.py`
- [X] T339 [P] [US15] Add a pre-commit hook that fails when `openapi.yaml` changed but the collection was not regenerated in `.pre-commit-config.yaml`
- [X] T340 [P] [US15] Ignore local environments and exported secrets (`*.local.postman_environment.json`, `*.secret.json`) in `FastApi/postman/.gitignore`
- [X] T341 [P] [US15] Write the Postman guide (import, choose an environment, get a token, run folders, run Newman, regenerate, publish, add a new endpoint) in `docs/postman.md`
- [ ] T342 [P] [US15] Extend the generator flows for `POST /v1/feedback` (up/down, reasons, consent flag) once US6 lands in `FastApi/postman/flows/feedback.yaml`
- [ ] T343 [P] [US15] Extend the generator flows for `/v1/history`, `/v1/saved` and `/v1/preferences` once US7 lands in `FastApi/postman/flows/conversation.yaml`
- [ ] T344 [P] [US15] Extend the generator flows for the review queue and `PATCH /v1/questions/{{id}}/transcript` once US12 lands in `FastApi/postman/flows/review.yaml`

**Checkpoint**: Every documented endpoint has a request, saved examples and assertions; the collection cannot drift from the contract

---

## Phase 18: User Story 16 - PDF intake, safe handling and the async pipeline (Source: F1 server side, F2, F3, F4 duplicates, F46, F47; READ_LEARN_FEATURE.md MVP) (Priority: P16)

**Goal**: Accept a PDF, validate it before any parser runs, scan and sandbox it, deduplicate it, and process it through an idempotent Celery pipeline that streams status events.

**Independent Test**: Upload a 20 MB PDF: the API answers 202 in under a second, a ZIP renamed `.pdf` is refused, an auto-open-JavaScript PDF is flagged and never executed, re-uploading the same file creates no second document, and a worker crash mid-run resumes without duplicate chunks.

### Tests for User Story 16 ⚠️ (write first, must FAIL)

- [X] T345 [P] [US16] Validation tests: magic bytes (`%PDF-`) win over extension and `Content-Type`, size, page-count and per-user quota limits, ZIP renamed `.pdf` rejected before any parser in `FastApi/tests/unit/pdf/test_validation.py`
- [X] T346 [P] [US16] Duplicate tests: same SHA-256 and owner returns the existing document and enqueues nothing; a different owner gets their own document in `FastApi/tests/unit/pdf/test_duplicates.py`
- [X] T347 [P] [US16] Active-content tests with crafted fixtures (`/JavaScript`, `/Launch`, `/EmbeddedFile` flagged, never executed, optionally stripped) in `FastApi/tests/unit/pdf/test_active_content.py`
- [X] T348 [P] [US16] Sandbox policy tests: no network, read-only filesystem, CPU/memory/wall-clock limits, rendered-pixel cap, one document per process, runaway job killed in `FastApi/tests/unit/pdf/test_sandbox.py`
- [X] T349 [P] [US16] Contract tests for `MalwareScanner` adapters (clean file, EICAR test string detected, scanner down fails closed) in `FastApi/tests/contract/test_malware_scanner_contract.py`
- [X] T350 [P] [US16] `IngestPdf` use-case tests with fakes for every port: stage order, status events, saga compensation deletes the half-built version, failure marks the document `failed` in `FastApi/tests/unit/pdf/test_ingest_pdf.py`
- [X] T351 [P] [US16] Idempotency tests: steps keyed by `(doc_id, version, step, pipeline_version)`, a re-run upserts instead of duplicating, transient errors retry with backoff, validation errors do not, repeated failures reach the dead-letter queue in `FastApi/tests/unit/pdf/test_pipeline_idempotency.py`
- [X] T352 [P] [US16] API tests: `POST /v1/documents` returns `202` with `document_id`, `GET /v1/documents` and `GET /v1/documents/{id}`, SSE stream of stage events, other users get 404 in `FastApi/tests/integration/pdf/test_documents_api.py`
- [X] T353 [P] [US16] tus resumable upload test: an upload interrupted at 60% resumes and completes, and the post-finish hook creates one document in `FastApi/tests/integration/pdf/test_tus_upload.py`

### Implementation for User Story 16

- [X] T354 [US16] Define domain entities `Document`, `DocumentVersion`, `DocumentStatus` (queued, scanning, reading, partial, ready, failed, quarantined) in `FastApi/app/domain/pdf/document.py`
- [X] T355 [P] [US16] Define ports `ObjectStore`, `MalwareScanner`, `PdfInspector`, `DocumentRepository`, `EventPublisher` in `FastApi/app/application/pdf/ports/`
- [X] T356 [P] [US16] Implement the validation service (magic bytes, size, pages, quotas) in `FastApi/app/application/pdf/services/validation.py`
- [X] T357 [P] [US16] Implement the MinIO `ObjectStore` adapter (content-addressed by SHA-256, immutable originals) in `FastApi/app/adapters/outbound/pdf/minio_object_store.py`
- [X] T358 [P] [US16] Implement the Postgres `DocumentRepository` and an Alembic migration (documents, document_versions, ingest_steps, dead_letters) in `FastApi/app/adapters/outbound/postgres/document_repository.py` and `FastApi/alembic/versions/`
- [X] T359 [P] [US16] Implement active-content detection and optional stripping with pikepdf in `FastApi/app/adapters/outbound/pdf/active_content.py`
- [X] T360 [P] [US16] Implement the ClamAV `MalwareScanner` adapter (clamd socket, fail closed) in `FastApi/app/adapters/outbound/pdf/clamav_scanner.py`
- [X] T361 [P] [US16] Implement the sandbox runner (non-root, read-only filesystem, no network, rlimits, pixel cap, one document per process) in `FastApi/app/adapters/outbound/pdf/sandbox.py` and the worker image in `FastApi/deploy/docker/pdf-worker.Dockerfile`
- [X] T362 [P] [US16] Implement the step ledger that makes every step idempotent and keys it by `(doc_id, version, step, pipeline_version)` in `FastApi/app/application/pdf/services/step_ledger.py`
- [X] T363 [US16] Implement the `IngestPdf` use case (validate, scan, inspect, parse, clean, chunk, embed, index) with saga compensation in `FastApi/app/application/pdf/use_cases/ingest_pdf.py`
- [X] T364 [P] [US16] Implement Celery tasks and the chain with isolated queues (`ingest` CPU, `gpu` OCR/layout/embeddings, `learn` low priority), retry policy and dead-letter handling in `FastApi/app/workers/pdf_tasks.py` and `FastApi/app/workers/celery_app.py`
- [X] T365 [P] [US16] Implement the Redis `EventPublisher` and the SSE endpoint `GET /v1/documents/{id}/events` in `FastApi/app/adapters/outbound/pdf/redis_events.py` and `FastApi/app/adapters/inbound/rest/document_events.py`
- [X] T366 [P] [US16] Implement the REST endpoints `POST /v1/documents`, `GET /v1/documents`, `GET /v1/documents/{id}` with ownership checks in `FastApi/app/adapters/inbound/rest/documents.py`
- [X] T367 [P] [US16] Implement the tus integration (tusd sidecar plus a post-finish webhook that creates the document) in `FastApi/app/adapters/inbound/rest/tus_hooks.py` and `FastApi/deploy/docker/docker-compose.yml`
- [X] T368 [P] [US16] Add the `pdf_ingest` settings (limits, ocr, chunking, retrieval, security, learning defaults from READ_LEARN_FEATURE.md section 8) in `FastApi/app/config.py`
- [X] T369 [P] [US16] Add ClamAV, tusd and the three worker queues as Kubernetes workloads with the restricted pod profile in `FastApi/deploy/k8s/base/pdf/`
- [X] T370 [P] [US16] Update OpenAPI, regenerate the Postman collection and add a `documents` flow (upload, poll, errors) in `FastApi/api-contracts/openapi.yaml` and `FastApi/postman/flows/documents.yaml`

**Checkpoint**: Intake is safe, idempotent and observable; documents reach `ready` through fakes or the first parsers

---

## Phase 19: User Story 17 - Ingestion quality harness and golden PDF corpus (Source: F50; READ_LEARN_FEATURE.md MVP and section 10) (Priority: P17)

**Goal**: Prove the reader reads well: a versioned golden PDF corpus with ground truth, stage metrics, CI gates and champion comparison, built before the parsers so they are written against it.

**Independent Test**: `make -C FastApi/ml pdf-eval` builds the corpus, runs the pipeline, writes metrics per slice and fails when a metric regresses; a deliberate regression in the header remover turns CI red.

### Tests for User Story 17 ⚠️ (write first, must FAIL)

- [X] T371 [P] [US17] Corpus builder tests: every slice is generated deterministically with its ground-truth JSON (clean book, two-column, tables, code, clean scan, phone photo, slides, mixed language, broken/huge, adversarial) in `FastApi/ml/pdf_golden/tests/test_corpus_builder.py`
- [X] T372 [P] [US17] Metric tests: character error rate, pairwise reading-order accuracy, TEDS, code exact-match, boilerplate leakage, chunk integrity, citation accuracy, recall@5 by PDF type, hidden-text recall in `FastApi/ml/pdf_golden/tests/test_pdf_metrics.py`
- [X] T373 [P] [US17] Gate tests (floors: CER ≤ 3%, reading order ≥ 95%, TEDS ≥ 0.85, code fidelity ≥ 95%, leakage ≤ 1%, chunk violations 0, citation accuracy ≥ 98%, recall@5 ≥ 0.85 per slice, hidden-text recall ≥ 95%) written to FAIL until the stages exist in `FastApi/ml/pdf_golden/tests/test_pdf_gates.py`
- [X] T374 [P] [US17] Champion comparison tests: a candidate must not regress any slice by more than 1 point in `FastApi/ml/pdf_golden/tests/test_pdf_champion.py`
- [X] T375 [P] [US17] Replay tests: stored traces re-run against a new pipeline version compare chunk ids and citations before the alias flips in `FastApi/ml/pdf_golden/tests/test_pdf_replay.py`

### Implementation for User Story 17

- [X] T376 [US17] Create the corpus builder that generates each slice with reportlab/pypdf (two-column text, ruled tables, code listings, rasterized clean scan and skewed phone photo, slide deck, English plus Spanish pages, damaged xref, 900-page file, white-on-white injection, decompression bomb) in `FastApi/ml/pdf_golden/build_corpus.py`
- [X] T377 [P] [US17] Write the ground-truth schema and files (text per block in reading order, tables as rows, code exact text, expected citations and recall questions) in `FastApi/ml/pdf_golden/ground_truth/` and `FastApi/ml/pdf_golden/schema.json`
- [X] T378 [P] [US17] Implement the stage metrics (CER, pairwise reading order, TEDS, code fidelity, boilerplate leakage, chunk integrity, citation accuracy, recall@5, hidden-text recall) in `FastApi/ml/pdf_golden/metrics.py`
- [X] T379 [P] [US17] Implement the evaluation runner that executes the pipeline over the corpus and writes `metrics.json` per slice in `FastApi/ml/pdf_golden/run_pdf_eval.py`
- [X] T380 [P] [US17] Implement champion/challenger comparison and slice-regression gating in `FastApi/ml/pdf_golden/compare.py`
- [X] T381 [P] [US17] Add property-based tests for the chunker invariants (text never lost, reordered or duplicated) with hypothesis in `FastApi/tests/unit/pdf/test_chunker_properties.py`
- [X] T382 [P] [US17] Implement trace replay for ingestion (chunk ids, citations) in `FastApi/ml/pdf_golden/replay.py`
- [X] T383 [P] [US17] Add `make pdf-corpus`, `make pdf-eval` and `make pdf-gates` in `FastApi/ml/Makefile`
- [X] T384 [P] [US17] Add the PDF quality workflow (build corpus, evaluate, upload metrics, gates reported red on purpose until each stage lands) in `.github/workflows/pdf-quality.yml`
- [ ] T385 [P] [US17] Track the corpus with DVC and freeze the ground truth with checksums in `FastApi/ml/pdf_golden/CHECKSUMS.json`

**Checkpoint**: The corpus, metrics and gates exist; stages are developed against them

---

## Phase 20: User Story 18 - Reading born-digital PDFs: routing, layout, code, cleanup and hidden-text safety (Source: F6, F7, F8, F9, F12, F14, F15, F16; READ_LEARN_FEATURE.md MVP) (Priority: P18)

**Goal**: Turn a born-digital PDF into trustworthy structured blocks (reading order, headings, code, tables kept as blocks) with page and position, cleaned of furniture and typography damage, with hidden text quarantined.

**Independent Test**: On the golden corpus the born-digital slices meet the reading-order, code-fidelity, boilerplate-leakage and hidden-text gates; scanned pages are reported "not readable yet".

### Tests for User Story 18 ⚠️ (write first, must FAIL)

- [ ] T386 [P] [US18] Page routing tests (born-digital, scanned, garbled, hybrid, grouping in order) in `FastApi/tests/unit/pdf/test_page_routing.py`
- [ ] T387 [P] [US18] Hidden-text tests (white on white, tiny, off-page, covered, invisible render mode only on born-digital pages, OCR layer on scans accepted) in `FastApi/tests/unit/pdf/test_hidden_text.py`
- [ ] T388 [P] [US18] Reading-order tests (two-column page reads the left column fully before the right; sidebars become `aside`) in `FastApi/tests/unit/pdf/test_reading_order.py`
- [ ] T389 [P] [US18] Layout tests (heading levels match the outline, captions linked to figures, footnotes) in `FastApi/tests/unit/pdf/test_layout.py`
- [ ] T390 [P] [US18] Boilerplate tests (repeated header/footer with digits normalised, > 40% of pages, watermark dropped, page label kept, copyright page to metadata) in `FastApi/tests/unit/pdf/test_boilerplate.py`
- [ ] T391 [P] [US18] Code-block tests (monospace detection, indentation kept, line numbers removed, curly quotes to ASCII, ligatures expanded, language detected and parse-verified) in `FastApi/tests/unit/pdf/test_code_blocks.py`
- [ ] T392 [P] [US18] Cleanup tests ("configu-" + "ration" joined, "well-known" untouched, soft hyphens, NFC, soft-wrapped lines joined, footnote markers linked) in `FastApi/tests/unit/pdf/test_cleanup.py`
- [ ] T393 [P] [US18] Metadata tests (title/author/dates from XMP then first heading, version detection, roman-numeral page labels stored with the PDF index, outline to section tree, links) in `FastApi/tests/unit/pdf/test_pdf_metadata.py`
- [ ] T394 [P] [US18] Prompt-injection phrase tests ("ignore previous instructions" detected and logged, never indexed) in `FastApi/tests/unit/pdf/test_injection_phrases.py`
- [ ] T395 [P] [US18] Contract tests every `PdfParser` adapter must pass (blocks carry page and bbox, deterministic order) in `FastApi/tests/contract/test_pdf_parser_contract.py`

### Implementation for User Story 18

- [ ] T396 [US18] Define value objects `BoundingBox`, `PageRange`, `SectionPath` and entities `Page`, `Block` in `FastApi/app/domain/pdf/layout.py`
- [ ] T397 [P] [US18] Implement `PageKind`, `PageStats`, `classify_page` and `group_pages` as pure functions in `FastApi/app/domain/pdf/page_kind.py`
- [ ] T398 [P] [US18] Implement the pypdfium2 `PdfInspector` (char count, image coverage, unmapped-glyph ratio per page) in `FastApi/app/adapters/outbound/pdf/pypdfium_inspector.py`
- [ ] T399 [P] [US18] Define the `PdfParser` port and the Strategy registry keyed by `PageKind` (composition root wires it) in `FastApi/app/application/pdf/ports/pdf_parser.py` and `FastApi/app/adapters/outbound/pdf/parser_registry.py`
- [ ] T400 [P] [US18] Implement the Docling layout-aware parser adapter for born-digital pages in `FastApi/app/adapters/outbound/pdf/docling_parser.py`
- [ ] T401 [P] [US18] Implement the pdfplumber column-aware fallback parser in `FastApi/app/adapters/outbound/pdf/pdfplumber_parser.py`
- [ ] T402 [P] [US18] Implement the reading-order service in `FastApi/app/application/pdf/services/reading_order.py`
- [ ] T403 [P] [US18] Implement block classification and outline-confirmed heading levels in `FastApi/app/application/pdf/services/layout.py`
- [ ] T404 [P] [US18] Implement the header, footer and boilerplate remover in `FastApi/app/application/pdf/services/boilerplate.py`
- [ ] T405 [P] [US18] Implement code-block detection, code-specific cleanup and language detection with Pygments/guesslang verified by tree-sitter in `FastApi/app/application/pdf/services/code_blocks.py`
- [ ] T406 [P] [US18] Implement the prose `Cleaner` (de-hyphenation, ligatures, NFC, line joining, footnotes) in `FastApi/app/application/pdf/services/cleaner.py`
- [ ] T407 [P] [US18] Implement the hidden-text detector (pixel sampling from the rendered page) and the quarantine store in `FastApi/app/domain/pdf/hidden_text.py` and `FastApi/app/adapters/outbound/pdf/quarantine.py`
- [ ] T408 [P] [US18] Implement the instruction-phrase detector that logs and flags injection attempts in `FastApi/app/application/pdf/services/injection_phrases.py`
- [ ] T409 [P] [US18] Implement the metadata, outline, link and page-label reader with pypdf in `FastApi/app/adapters/outbound/pdf/pdf_metadata.py`
- [ ] T410 [P] [US18] Mark scanned and garbled pages "not readable yet" and publish the page counts until OCR lands (US22) in `FastApi/app/application/pdf/services/unreadable_pages.py`
- [ ] T411 [P] [US18] Wire the parsers, cleaner and detectors into the composition root and the Celery steps in `FastApi/app/bootstrap.py` and `FastApi/app/workers/pdf_tasks.py`

**Checkpoint**: Born-digital PDFs are read into clean structured blocks

---

## Phase 21: User Story 19 - Structure-aware chunking, provenance and the dense index (Source: F18, F20, F21 (dense), F31; READ_LEARN_FEATURE.md MVP) (Priority: P19)

**Goal**: Chunk blocks where the document splits, attach full provenance to every chunk, index them with versioned embeddings, and make a new upload answerable within minutes with no training.

**Independent Test**: No chunk crosses a heading or splits a code block (property-tested); every chunk has doc, version, page, bbox and section path; a question asked minutes after upload is answered with no training run.

### Tests for User Story 19 ⚠️ (write first, must FAIL)

- [ ] T412 [P] [US19] Chunker tests: code is atomic and keeps its section path, a new heading never leaks into the previous section, no prose chunk exceeds the token budget, oversized code splits only at blank lines, overlap applies to prose only in `FastApi/tests/unit/pdf/test_chunker.py`
- [ ] T413 [P] [US19] Provenance tests: every chunk carries `doc_id`, `doc_version`, `page_index`, `page_label`, `bbox` list, `section_path`, `chunk_type`, `language`, `pipeline_version`, `embedder_version`, `owner`, `acl`, `license`, `valid_from/valid_to`, `content_hash` in `FastApi/tests/unit/pdf/test_provenance.py`
- [ ] T414 [P] [US19] Deterministic id tests: ids hash document, page, position and text so re-runs upsert and never duplicate in `FastApi/tests/unit/pdf/test_chunk_ids.py`
- [ ] T415 [P] [US19] Index tests: batch upsert, delete one version with a single filter, `valid_to` set on supersession, one collection per embedder version behind an alias in `FastApi/tests/contract/test_pdf_index_contract.py`
- [ ] T416 [P] [US19] Instant-learning test: upload then ask within the same test run and get a cited answer with no training job in `FastApi/tests/integration/pdf/test_instant_learning.py`

### Implementation for User Story 19

- [ ] T417 [US19] Define the `Chunk` entity and `ChunkType` (text, code, table, summary, figure_caption) in `FastApi/app/domain/pdf/chunk.py`
- [ ] T418 [P] [US19] Implement the structure-aware chunker (headings first, then paragraphs, atomic code and tables, token budget from the embedder tokenizer, sentence-boundary fallback) in `FastApi/app/application/pdf/services/chunker.py`
- [ ] T419 [P] [US19] Implement the deterministic chunk id and the content hash in `FastApi/app/domain/pdf/chunk_id.py`
- [ ] T420 [P] [US19] Implement the provenance payload builder in `FastApi/app/application/pdf/services/provenance.py`
- [ ] T421 [P] [US19] Extend the Qdrant adapter with the document payload schema, payload indexes and `delete_version(doc_id, version)` in `FastApi/app/adapters/outbound/qdrant/document_index.py` — build on the US31 point store (T584) and collection specs (T581)
- [ ] T422 [P] [US19] Implement embedder-versioned collections and the alias switch for the PDF index in `FastApi/app/adapters/outbound/qdrant/versioned_documents.py` — build on the US31 point store (T584) and collection specs (T581)
- [ ] T423 [P] [US19] Implement batch embedding and indexing with status events in `FastApi/app/application/pdf/use_cases/index_document.py`
- [ ] T424 [P] [US19] Expose `chunk_type`, `page_label` and `section_path` in the retrieval results for citations in `FastApi/app/application/pdf/ports/vector_store.py`

**Checkpoint**: Chunks are structurally sound, traceable and searchable minutes after upload

---

## Phase 22: User Story 20 - Scoped, cited answers, library backend, deletion and audit (Source: F24, F25, F30, F40 (personal ACL), F41; READ_LEARN_FEATURE.md MVP) (Priority: P20)

**Goal**: Answer only from the scope the user chose, cite pages with highlightable boxes, say "not in this PDF" instead of guessing, keep one user from ever retrieving another user's chunks, and make deletion real and audited.

**Independent Test**: With scope = document A no chunk of document B is ever returned; every answer step carries page citations with boxes and quotes; Kafka asked of the Spring guide abstains; deleting a document removes file, chunks, summaries and cached answers.

### Tests for User Story 20 ⚠️ (write first, must FAIL)

- [ ] T425 [P] [US20] Scope and ACL specification tests (document, collection, library, everything; `acl` match, `valid_to` null, `doc_id` in scope) in `FastApi/tests/unit/pdf/test_scope_specification.py`
- [ ] T426 [P] [US20] Security contract test every `VectorSearcher` must pass: user B never retrieves user A's chunks, even in "Everything" scope in `FastApi/tests/contract/test_acl_isolation_contract.py`
- [ ] T427 [P] [US20] Citation tests: chunk ids become `{doc, page_index, page_label, bbox, quote}`, quotes are short, a cited page contains the quoted text in `FastApi/tests/unit/pdf/test_citations.py`
- [ ] T428 [P] [US20] Abstain tests: best reranked score below the threshold returns "not in this PDF" with an offer to widen scope; general knowledge only when enabled and visibly marked without citations in `FastApi/tests/unit/pdf/test_abstain.py`
- [ ] T429 [P] [US20] `AskAboutDocuments` tests (scope persists across follow-ups, open document is the default scope, guardrails and the grounded prompt still apply) in `FastApi/tests/unit/pdf/test_ask_about_documents.py`
- [ ] T430 [P] [US20] Deletion saga tests: file, page images, chunks and vectors, summaries, glossary entries sourced only from the document, cached answers and derived training examples are purged after the soft-delete window in `FastApi/tests/unit/pdf/test_delete_document.py`
- [ ] T431 [P] [US20] Audit tests: administrative reads and deletions are recorded with who and when, and decision traces store `doc_ids` but never content in `FastApi/tests/unit/pdf/test_audit.py`
- [ ] T432 [P] [US20] API tests for `POST /v1/ask` (text or `audio_id`, scope variants), `DELETE /v1/documents/{id}`, collections and tags in `FastApi/tests/integration/pdf/test_ask_and_library_api.py`

### Implementation for User Story 20

- [ ] T433 [US20] Define the `Scope` value object and the scope/ACL `Specification` in `FastApi/app/domain/pdf/scope.py`
- [ ] T434 [P] [US20] Enforce the mandatory scope filter inside the Qdrant adapter (never only in the UI) in `FastApi/app/adapters/outbound/qdrant/document_index.py` — build on the US31 point store (T584) and collection specs (T581)
- [ ] T435 [P] [US20] Implement the `Citation` builder and the page-label aware citation text in `FastApi/app/application/pdf/services/citations.py`
- [ ] T436 [P] [US20] Implement the `AskAboutDocuments` use case (scope, hybrid retrieval, rerank, grounded generation, citations, abstain) in `FastApi/app/application/pdf/use_cases/ask_about_documents.py`
- [ ] T437 [P] [US20] Implement `POST /v1/ask` with `scope`, `scope_used`, `citations`, `gate` and `trace_id` in `FastApi/app/adapters/inbound/rest/ask.py`
- [ ] T438 [P] [US20] Implement collections, tags and ownership in the repository and API in `FastApi/app/application/pdf/use_cases/manage_library.py` and `FastApi/app/adapters/inbound/rest/library.py`
- [ ] T439 [P] [US20] Implement the `DeleteDocument` saga with a soft-delete window and the purge job in `FastApi/app/application/pdf/use_cases/delete_document.py` and `FastApi/app/workers/purge_tasks.py`
- [ ] T440 [P] [US20] Implement `DocumentDeleted` handling that invalidates the semantic cache by document version in `FastApi/app/application/pdf/services/cache_invalidation.py`
- [ ] T441 [P] [US20] Implement the audit log (table, repository, query endpoint for admins) in `FastApi/app/adapters/outbound/postgres/audit_repository.py` and `FastApi/app/adapters/inbound/rest/audit.py`
- [ ] T442 [P] [US20] Add per-tenant retention policy settings in `FastApi/app/config.py`
- [ ] T443 [P] [US20] Record `doc_ids` (not content) in decision traces in `FastApi/app/adapters/outbound/tracing/`
- [ ] T444 [P] [US20] Update OpenAPI, regenerate the Postman collection and add `ask_documents` and `delete_document` flows in `FastApi/api-contracts/openapi.yaml` and `FastApi/postman/flows/ask_documents.yaml`

**Checkpoint**: Answers are scoped, cited, honest and deletable

---

## Phase 23: User Story 21 - Library, upload, progress and viewer on web, Android and iOS (Source: F1 clients, F40 UI, F42, F43, F44 (ask); READ_LEARN_FEATURE.md MVP) (Priority: P21)

**Goal**: Let users add PDFs from every client, watch them being read, ask about one document by voice or text, and tap a citation to see the highlighted passage in a viewer.

**Independent Test**: On each client: share a PDF to the app, watch the stepper reach "Pages 1–40 ready", ask a question, and tap "p. 42" to open the page with the passage outlined.

### Tests for User Story 21 ⚠️ (write first, must FAIL)

- [ ] T445 [P] [US21] Design the library, upload-progress and viewer screens in light and dark in `UX/UI /library.html` and `UX/UI /viewer.html` (extend the existing design tokens)
- [ ] T446 [P] [US21] Angular specs: library list and filters, upload with drag and drop and resume, progress stepper from SSE, error actions (retry, password, re-scan, remove) in `Angular/src/app/library/library.component.spec.ts`
- [ ] T447 [P] [US21] Angular viewer specs: citation chip opens the page and draws the stored boxes, next/previous citation, select text and "Explain this paragraph" in `Angular/src/app/viewer/viewer.component.spec.ts`
- [ ] T448 [P] [US21] Bounding-box conversion tests for every platform (points, top-left origin to each page space) in `Angular/src/app/viewer/bbox.spec.ts`, `Android/app/src/test/kotlin/com/voiceassistant/viewer/BoundingBoxTest.kt` and `IOS/VoiceAssistantTests/BoundingBoxTests.swift`
- [ ] T449 [P] [US21] Android ViewModel tests for upload (WorkManager, resume), progress and library in `Android/app/src/test/kotlin/com/voiceassistant/ui/library/LibraryViewModelTest.kt`
- [ ] T450 [P] [US21] iOS ViewModel tests for upload (background URLSession, resume), progress and library in `IOS/VoiceAssistantTests/LibraryViewModelTests.swift`
- [ ] T451 [P] [US21] Android and iOS UI tests: share target, stepper, citation jump in `Android/app/src/androidTest/kotlin/com/voiceassistant/LibraryScreenTest.kt` and `IOS/VoiceAssistantUITests/LibraryUITests.swift`
- [ ] T452 [P] [US21] Playwright E2E: upload, wait for pages ready, ask, click the citation chip and see the highlight in `Angular/e2e/pdf-flow.spec.ts`

### Implementation for User Story 21

- [ ] T453 [US21] Generate the typed documents, ask and events clients from the updated OpenAPI into `Angular/src/app/core/api/`, `Android/app/src/main/kotlin/com/voiceassistant/data/api/` and `IOS/VoiceAssistant/Data/API/`
- [ ] T454 [P] [US21] Implement the Angular library page (list, status, tags, collections, quality flags) in `Angular/src/app/library/library.component.ts`
- [ ] T455 [P] [US21] Implement the Angular upload service with drag and drop and tus resumable upload in `Angular/src/app/library/upload.service.ts`
- [ ] T456 [P] [US21] Implement the progress stepper (Uploaded, Checking, Reading pages n/N, OCR, Indexing, Ready) and "Ask now" for partial documents in `Angular/src/app/library/progress-stepper.component.ts`
- [ ] T457 [P] [US21] Implement the PDF.js viewer with the highlight overlay and citation navigation in `Angular/src/app/viewer/viewer.component.ts`
- [ ] T458 [P] [US21] Implement the scope selector (This PDF, A collection, My library, Everything) and citation chips in the answer card in `Angular/src/app/conversation/scope-selector.component.ts` and `Angular/src/app/conversation/citation-chips.component.ts`
- [ ] T459 [P] [US21] Implement Android: Storage Access Framework picker, `application/pdf` share target and WorkManager tus upload in `Android/app/src/main/kotlin/com/voiceassistant/ui/library/` and `Android/app/src/main/AndroidManifest.xml`
- [ ] T460 [P] [US21] Implement Android: library, progress and PdfRenderer viewer with a Compose highlight overlay in `Android/app/src/main/kotlin/com/voiceassistant/ui/library/` and `Android/app/src/main/kotlin/com/voiceassistant/ui/viewer/`
- [ ] T461 [P] [US21] Implement iOS: `.fileImporter`, Share Extension and background `URLSession` tus upload in `IOS/VoiceAssistant/UI/Library/` and `IOS/ShareExtension/`
- [ ] T462 [P] [US21] Implement iOS: library, progress and PDFKit viewer with highlight annotations in `IOS/VoiceAssistant/UI/Library/` and `IOS/VoiceAssistant/UI/Viewer/`
- [ ] T463 [P] [US21] Implement push notification on completion (FCM and APNs) behind a `Notifier` port in `FastApi/app/application/pdf/ports/notifier.py` and `FastApi/app/adapters/outbound/pdf/push_notifier.py`
- [ ] T464 [P] [US21] Add voice and text "ask this document" with the open document as the default scope on all three clients in `Angular/src/app/conversation/`, `Android/app/src/main/kotlin/com/voiceassistant/ui/ask/` and `IOS/VoiceAssistant/UI/Ask/`

**Checkpoint**: Users can add, watch, ask about and verify PDFs on every client

---

## Phase 24: User Story 22 - OCR, tables, figures, languages and encrypted or damaged PDFs (Source: F5, F10, F11, F13 (captions), F17; READ_LEARN_FEATURE.md v1) (Priority: P22)

**Goal**: Read pages that are pictures, rebuild tables, make figures findable by caption, handle several languages, and cope with password-protected or damaged files.

**Independent Test**: The scanned appendix is indexed with per-page confidence, tables come out as Markdown rows (TEDS ≥ 0.85), an encrypted PDF prompts for a password that is never stored, and a damaged xref is repaired.

### Tests for User Story 22 ⚠️ (write first, must FAIL)

- [ ] T465 [P] [US22] OCR tests: 300 DPI render, deskew and denoise, per-word confidence and page mean, pages under 0.80 flagged "low OCR quality" and excluded from training, word boxes kept in `FastApi/tests/unit/pdf/test_ocr.py`
- [ ] T466 [P] [US22] Contract tests for every `OcrEngine` adapter in `FastApi/tests/contract/test_ocr_engine_contract.py`
- [ ] T467 [P] [US22] Table tests: ruled table to Markdown and JSON rows, merged cells, tables continued across pages stitched by header in `FastApi/tests/unit/pdf/test_tables.py`
- [ ] T468 [P] [US22] Figure tests: image/vector extraction, caption linking by proximity, diagram OCR text, cropped region kept in `FastApi/tests/unit/pdf/test_figures.py`
- [ ] T469 [P] [US22] Language tests: per-page detection, English with a Spanish appendix tagged `en` and `es`, code kept separate from natural language in `FastApi/tests/unit/pdf/test_language.py`
- [ ] T470 [P] [US22] Encrypted/damaged tests: password asked, decrypted in memory only and never logged or stored, copy restrictions respected until the uploader attests rights, xref repair, failed pages listed in `FastApi/tests/unit/pdf/test_encrypted_and_damaged.py`

### Implementation for User Story 22

- [ ] T471 [US22] Define the `OcrEngine` and `TableExtractor` ports in `FastApi/app/application/pdf/ports/ocr_engine.py` and `FastApi/app/application/pdf/ports/table_extractor.py`
- [ ] T472 [P] [US22] Implement page rendering at 300 DPI with deskew, denoise and adaptive binarization in `FastApi/app/adapters/outbound/pdf/page_renderer.py`
- [ ] T473 [P] [US22] Implement the OCRmyPDF/Tesseract `OcrEngine` adapter in `FastApi/app/adapters/outbound/pdf/tesseract_ocr.py`
- [ ] T474 [P] [US22] Implement the PaddleOCR/docTR alternative adapter behind the same port in `FastApi/app/adapters/outbound/pdf/paddle_ocr.py`
- [ ] T475 [P] [US22] Implement the low-confidence flag and the "low OCR quality" document warning in `FastApi/app/application/pdf/services/ocr_quality.py`
- [ ] T476 [P] [US22] Implement the Docling table extractor with a pdfplumber/Camelot fallback and cross-page stitching in `FastApi/app/adapters/outbound/pdf/table_extractor.py`
- [ ] T477 [P] [US22] Implement figure extraction, caption linking and diagram OCR in `FastApi/app/adapters/outbound/pdf/figure_extractor.py`
- [ ] T478 [P] [US22] Implement per-page language detection with lingua and OCR language-pack selection in `FastApi/app/application/pdf/services/language.py`
- [ ] T479 [P] [US22] Implement the password flow (`POST /v1/documents/{id}/password`, in-memory decryption, never persisted) in `FastApi/app/adapters/inbound/rest/document_password.py` and `FastApi/app/adapters/outbound/pdf/pdf_decryptor.py`
- [ ] T480 [P] [US22] Implement the xref repair with qpdf/pikepdf and the OCR fallback for unreadable pages in `FastApi/app/adapters/outbound/pdf/pdf_repair.py`
- [ ] T481 [P] [US22] Route scanned, garbled and hybrid pages to the OCR strategies through the parser registry on the `gpu` queue in `FastApi/app/adapters/outbound/pdf/parser_registry.py` and `FastApi/app/workers/pdf_tasks.py`
- [ ] T482 [P] [US22] Add OCR, TEDS, reading-order and language slices to the golden corpus gates in `FastApi/ml/pdf_golden/run_pdf_eval.py`

**Checkpoint**: Scans, tables, figures, other languages and protected files are read

---

## Phase 25: User Story 23 - Advanced retrieval: small-to-big, hybrid search, multi-representation and progressive indexing (Source: F19, F21 (hybrid), F22, F23, F29; READ_LEARN_FEATURE.md v1) (Priority: P23)

**Goal**: Match precisely and answer with context, find exact identifiers as well as meaning, index tables and figures several ways, make pages searchable as soon as each batch is embedded, and do table arithmetic in code.

**Independent Test**: `@Transactional` and "transactional annotation" reach the same chunk (top 3); a 120-page PDF is searchable from page 1–40 while OCR still runs; "sum the Q3 column" is computed with pandas and cited.

### Tests for User Story 23 ⚠️ (write first, must FAIL)

- [ ] T483 [P] [US23] Small-to-big tests: a small child chunk matches and the parent section reaches the generator, breadcrumb context header embedded in `FastApi/tests/unit/pdf/test_small_to_big.py`
- [ ] T484 [P] [US23] Hybrid tests: exact token `@Transactional` ranks the exact chunk in the top 3 with dense plus sparse and RRF in `FastApi/tests/integration/pdf/test_hybrid_documents.py`
- [ ] T485 [P] [US23] Multi-representation tests: a table is stored as Markdown, a summary and one sentence per row; a row question cites the table and highlights the row in `FastApi/tests/unit/pdf/test_multi_representation.py`
- [ ] T486 [P] [US23] Progressive indexing tests: batches become searchable as embedded, a later failure leaves the document `partial`, a new version re-embeds only changed pages in `FastApi/tests/unit/pdf/test_progressive_indexing.py`
- [ ] T487 [P] [US23] Table-question tests: routing of table-style questions, arithmetic via a bounded tool never by the LLM, result shown with its citation in `FastApi/tests/unit/pdf/test_table_questions.py`

### Implementation for User Story 23

- [ ] T488 [US23] Implement parent/child chunk linking and the contextual breadcrumb header in `FastApi/app/application/pdf/services/small_to_big.py`
- [ ] T489 [P] [US23] Add sparse/BM25 vectors with server-side RRF fusion to the PDF index in `FastApi/app/adapters/outbound/qdrant/document_index.py` — build on the US31 point store (T584) and collection specs (T581)
- [ ] T490 [P] [US23] Implement multi-representation indexing for tables and figures in `FastApi/app/application/pdf/services/multi_representation.py`
- [ ] T491 [P] [US23] Implement batch-wise indexing with the `partial` status and per-page content hashes in `FastApi/app/application/pdf/use_cases/index_document.py`
- [ ] T492 [P] [US23] Implement the table-question router and the bounded `table_calculator` tool (pandas) in `FastApi/app/application/pdf/services/table_questions.py` and `FastApi/app/application/pdf/services/tools/table_calculator.py`
- [ ] T493 [P] [US23] Add retrieval settings (`dense_top 50`, `sparse_top 50`, `fused_top 20`, `final_top 5`) and recall@5 per PDF type to the gates in `FastApi/app/config.py` and `FastApi/ml/pdf_golden/run_pdf_eval.py`

**Checkpoint**: Retrieval is precise, contextual and available early

---

## Phase 26: User Story 24 - Summaries of sections, chapters and documents (Source: F26; READ_LEARN_FEATURE.md v1) (Priority: P24)

**Goal**: Provide short, page-referenced summaries built bottom-up over the section tree, available instantly and readable aloud.

**Independent Test**: "Summarize chapter 3" returns five bullets, each ending with page references; "what is this PDF about" is answered from stored summaries.

### Tests for User Story 24 ⚠️ (write first, must FAIL)

- [ ] T494 [P] [US24] Map-reduce summary tests: leaf sections, then chapters, then the document; every bullet carries page references in `FastApi/tests/unit/pdf/test_summaries.py`
- [ ] T495 [P] [US24] Option tests: length, audience, bullets or prose, shorter spoken version in `FastApi/tests/unit/pdf/test_summary_options.py`
- [ ] T496 [P] [US24] Stored-summary tests: `chunk_type: summary` retrieval answers "what is this PDF about" without re-summarizing in `FastApi/tests/unit/pdf/test_summary_retrieval.py`

### Implementation for User Story 24

- [ ] T497 [US24] Implement the bottom-up summarizer over the section tree in `FastApi/app/application/pdf/use_cases/summarize_document.py`
- [ ] T498 [P] [US24] Store summaries as `chunk_type: summary` chunks on the `learn` queue in `FastApi/app/workers/learn_tasks.py`
- [ ] T499 [P] [US24] Add `POST /v1/documents/{id}/summary` with length and audience options in `FastApi/app/adapters/inbound/rest/summaries.py`
- [ ] T500 [P] [US24] Implement the spoken-summary variant for voice mode in `FastApi/app/application/pdf/services/spoken_summary.py`
- [ ] T501 [P] [US24] Show and play summaries on all three clients in `Angular/src/app/library/`, `Android/app/src/main/kotlin/com/voiceassistant/ui/library/` and `IOS/VoiceAssistant/UI/Library/`

**Checkpoint**: Documents can be summarized with traceable pages

---

## Phase 27: User Story 25 - Learning from PDFs: glossary, synthetic Q&A, intent mining and auto-tags (Source: F32, F33, F34, F35; READ_LEARN_FEATURE.md v1) (Priority: P25)

**Goal**: Learn each PDF's vocabulary and structure and turn it into reviewed training assets: glossary candidates, round-trip-filtered synthetic questions, mined intent utterances and metadata tags.

**Independent Test**: Approved terms correct the next transcription ("dispatcher servlet" becomes `DispatcherServlet`); only synthetic questions whose source chunk ranks in the top 5 survive; code with Spring imports gets `framework=spring`.

### Tests for User Story 25 ⚠️ (write first, must FAIL)

- [ ] T502 [P] [US25] Glossary mining tests: code-font tokens, "Full Name (ABC)" acronyms, bold first mentions, frequent phrases, scoring, dedupe against the existing glossary in `FastApi/ml/tests/test_glossary_mining.py`
- [ ] T503 [P] [US25] Glossary activation tests: an approved term reaches STT hotwords, the corrector, slot gazetteers and query synonyms, and biases speech while the document is open in `FastApi/ml/tests/test_glossary_activation.py`
- [ ] T504 [P] [US25] Synthetic Q&A tests: 3 to 5 questions per good chunk, the round-trip filter keeps only top-5 sources, failures go to review, hard negatives from neighbours, caps per document, `origin: synthetic_pdf` with `source_doc_id` in `FastApi/ml/tests/test_synthetic_qa.py`
- [ ] T505 [P] [US25] Intent-mining tests: "How to ..." to `CREATE_CODE_ARTIFACT`, "What is ..." to `EXPLAIN_CONCEPT`, "Troubleshooting ..." to `DEBUG_ERROR` with slots filled and sent to the labeling queue in `FastApi/ml/tests/test_intent_mining.py`
- [ ] T506 [P] [US25] Auto-tagging tests: imports and annotations give `language`, `framework`, `artifact_type`, `version`; unlabeled clusters propose new taxonomy values in `FastApi/ml/tests/test_auto_tagging.py`

### Implementation for User Story 25

- [ ] T507 [US25] Define the `GlossaryRepository` and `SyntheticQaGenerator` ports in `FastApi/app/application/pdf/ports/glossary_repository.py` and `FastApi/app/application/pdf/ports/synthetic_qa_generator.py`
- [ ] T508 [P] [US25] Implement glossary candidate mining (code font, acronyms, emphasis, KeyBERT) and scoring in `FastApi/ml/pdf_learning/glossary_mining.py`
- [ ] T509 [P] [US25] Implement the glossary review queue and approval API feeding `FastApi/ml/glossary/terms.yaml` and per-user glossaries in `FastApi/app/adapters/inbound/rest/glossary_review.py` and `FastApi/app/application/pdf/use_cases/approve_glossary_term.py`
- [ ] T510 [P] [US25] Bias faster-whisper with the open document's top terms (`hotwords`, `initial_prompt`) for the session in `FastApi/app/adapters/outbound/stt/faster_whisper_transcriber.py`
- [ ] T511 [P] [US25] Implement the synthetic Q&A generator with a local LLM and the round-trip filter in `FastApi/ml/pdf_learning/synthetic_qa.py`
- [ ] T512 [P] [US25] Implement intent utterance mining and export to the labeling queue in `FastApi/ml/pdf_learning/intent_mining.py`
- [ ] T513 [P] [US25] Implement auto-tagging (rules plus the slot classifier) and taxonomy proposals in `FastApi/app/application/pdf/services/auto_tagging.py`
- [ ] T514 [P] [US25] Run the learning assets as Celery tasks on the low-priority `learn` queue in `FastApi/app/workers/learn_tasks.py`
- [ ] T515 [P] [US25] Add the learning assets to dataset versioning with lineage (`source_doc_id`) in `FastApi/ml/pipelines/build_dataset.py`

**Checkpoint**: Every PDF improves vocabulary and training data, with a human in the loop

---

## Phase 28: User Story 26 - Voice commands, accessibility and offline resilience (Source: F44 (commands), F45; READ_LEARN_FEATURE.md v1) (Priority: P26)

**Goal**: Operate documents hands-free and keep the library usable for screen-reader users and on weak or no connections.

**Independent Test**: With a document open, "go to the page about transactions" and "read the summary" work by voice; offline the library and summaries stay readable and queued uploads start when the network returns.

### Tests for User Story 26 ⚠️ (write first, must FAIL)

- [ ] T516 [P] [US26] Voice-command tests: "ask this PDF ...", "go to the page about ...", "read the summary", "next citation" map to intents and actions in `FastApi/tests/unit/pdf/test_voice_commands.py`
- [ ] T517 [P] [US26] Read-aloud tests: code blocks are announced instead of read symbol by symbol in `FastApi/tests/unit/pdf/test_read_aloud.py`
- [ ] T518 [P] [US26] Accessibility tests: tagged-PDF structure and alt text exposed, text-only reading view in `FastApi/tests/unit/pdf/test_text_only_view.py`
- [ ] T519 [P] [US26] Offline tests per client: library, summaries and recent answers available offline, uploads queued and resumed in `Angular/src/app/library/offline.spec.ts`, `Android/app/src/test/kotlin/com/voiceassistant/ui/library/OfflineTest.kt` and `IOS/VoiceAssistantTests/OfflineTests.swift`

### Implementation for User Story 26

- [ ] T520 [US26] Add the document voice intents (`DOC_ASK`, `DOC_GOTO`, `DOC_SUMMARY`, `DOC_NEXT_CITATION`) to the taxonomy and handlers in `FastApi/ml/data/taxonomy.yaml` and `FastApi/app/application/pdf/services/voice_commands.py`
- [ ] T521 [P] [US26] Implement the text-only reading view endpoint and tagged-PDF/alt-text extraction in `FastApi/app/adapters/inbound/rest/reading_view.py` and `FastApi/app/adapters/outbound/pdf/tagged_pdf.py`
- [ ] T522 [P] [US26] Implement TTS read-aloud that announces code blocks on all three clients in `Angular/src/app/viewer/`, `Android/app/src/main/kotlin/com/voiceassistant/ui/viewer/` and `IOS/VoiceAssistant/UI/Viewer/`
- [ ] T523 [P] [US26] Implement offline storage and the upload queue on web (service worker, IndexedDB), Android (Room, WorkManager) and iOS (SwiftData, background tasks) in `Angular/src/app/library/offline.service.ts`, `Android/app/src/main/kotlin/com/voiceassistant/data/offline/` and `IOS/VoiceAssistant/Data/Offline/`
- [ ] T524 [P] [US26] Use compressed page thumbnails and resumable uploads on weak connections in `FastApi/app/adapters/outbound/pdf/thumbnails.py` and the client upload services

**Checkpoint**: Documents work hands-free, accessibly and offline

---

## Phase 29: User Story 27 - Document versions, pipeline versioning, observability and quotas (Source: F4 versions, F48, F49; READ_LEARN_FEATURE.md v1) (Priority: P27)

**Goal**: Keep a history of revisions, reprocess documents safely when the reader improves, and know what ingestion costs and where it fails.

**Independent Test**: Uploading `api-spec-v2.pdf` after v1 asks "Replace or keep both?"; a parser upgrade re-indexes documents overnight and flips the alias only if the golden gates pass; a quota breach shows a clear message.

### Tests for User Story 27 ⚠️ (write first, must FAIL)

- [ ] T525 [P] [US27] Version tests: same title lineage becomes a new version, old chunks get `valid_to`, default queries use the latest, "in version 1" still works in `FastApi/tests/unit/pdf/test_document_versions.py`
- [ ] T526 [P] [US27] Reprocessing tests: most-recently-used first, new index version built, alias flips only when the golden set passes, rollback in `FastApi/tests/unit/pdf/test_reprocessing.py`
- [ ] T527 [P] [US27] Metrics and quota tests: per-stage latency and failure reasons, documents/pages/storage quotas, rate limits, clear user messages in `FastApi/tests/unit/pdf/test_quotas_and_metrics.py`

### Implementation for User Story 27

- [ ] T528 [US27] Implement version lineage detection and the "replace or keep both" decision in `FastApi/app/application/pdf/use_cases/register_version.py`
- [ ] T529 [P] [US27] Implement `POST /v1/documents/{id}/reindex` and the background re-index job with alias flip gated by the golden corpus in `FastApi/app/adapters/inbound/rest/reindex.py` and `FastApi/app/workers/reindex_tasks.py`
- [ ] T530 [P] [US27] Store `pipeline_version` on every chunk and compare pipeline versions in `FastApi/app/application/pdf/services/pipeline_versions.py`
- [ ] T531 [P] [US27] Implement per-stage Prometheus metrics (latency, pages per second, failure reasons, OCR share, GPU use, queue depth) and cost per document in `FastApi/app/adapters/outbound/pdf/metrics.py`
- [ ] T532 [P] [US27] Implement per-user quotas and rate limits with user-facing errors in `FastApi/app/application/pdf/services/quotas.py` and `FastApi/app/adapters/inbound/rest/errors.py`
- [ ] T533 [P] [US27] Add the ingestion dashboards and alerts in `FastApi/deploy/k8s/observability/dashboards/pdf-ingestion.json` and `FastApi/deploy/k8s/observability/alerts/pdf-ingestion.yaml`
- [ ] T534 [P] [US27] Carry `doc_id` and `pipeline_version` in traces in `FastApi/app/adapters/outbound/tracing/`

**Checkpoint**: Documents evolve safely and ingestion is measurable

---

## Phase 30: User Story 28 - Structured extraction, cross-document Q&A and version diff (Source: F27, F28; READ_LEARN_FEATURE.md v2) (Priority: P28)

**Goal**: Turn document content into validated data and compare or combine documents with citations to each.

**Independent Test**: "List all configuration properties" returns schema-valid JSON where every record has a page; "what changed between v1 and v2" lists added, removed and changed sections with citations to both versions.

### Tests for User Story 28 ⚠️ (write first, must FAIL)

- [ ] T535 [P] [US28] Extraction tests: output validates against the supplied JSON Schema, invalid output is retried, every record keeps its page, CSV and JSON export in `FastApi/tests/unit/pdf/test_structured_extraction.py`
- [ ] T536 [P] [US28] Cross-document tests: per-document retrieval quota, answers grouped by document in `FastApi/tests/unit/pdf/test_cross_document.py`
- [ ] T537 [P] [US28] Diff tests: sections aligned by title and semantic similarity, added/removed/changed summarized with citations to both versions in `FastApi/tests/unit/pdf/test_version_diff.py`

### Implementation for User Story 28

- [ ] T538 [US28] Implement the schema-driven extractor with validation and retry in `FastApi/app/application/pdf/use_cases/extract_structured.py`
- [ ] T539 [P] [US28] Add `POST /v1/documents/{id}/extract` with CSV and JSON export in `FastApi/app/adapters/inbound/rest/extraction.py`
- [ ] T540 [P] [US28] Implement per-document quota retrieval for cross-document questions in `FastApi/app/application/pdf/services/cross_document.py`
- [ ] T541 [P] [US28] Implement version alignment and the diff summarizer in `FastApi/app/application/pdf/use_cases/diff_versions.py`
- [ ] T542 [P] [US28] Add extraction and diff views on the web client in `Angular/src/app/library/extract.component.ts` and `Angular/src/app/library/diff.component.ts`

**Checkpoint**: Documents become data and can be compared

---

## Phase 31: User Story 29 - Knowledge graph, document quality, freshness and vision reading (Source: F36, F37, F38, F13 (descriptions) and the optional vision-language page reader; READ_LEARN_FEATURE.md v2) (Priority: P29)

**Goal**: Capture relations, learn which documents deserve trust, prefer current versions and read figure-heavy pages with a local vision-language model.

**Independent Test**: "What does UserController depend on" returns `UserService`; a scanned PDF with many thumbs-down is flagged and excluded from training; answers state the version used and warn when a newer one exists.

### Tests for User Story 29 ⚠️ (write first, must FAIL)

- [ ] T543 [P] [US29] Graph tests: entities and relations extracted from code and prose, query expansion controller to service to repository, relationship questions in `FastApi/tests/unit/pdf/test_knowledge_graph.py`
- [ ] T544 [P] [US29] Quality-score tests: helpful rate, copy-code rate, abstain rate, low-OCR share and duplicate rate give a `quality_score` used as a mild ranking feature and a training gate in `FastApi/tests/unit/pdf/test_document_quality.py`
- [ ] T545 [P] [US29] Freshness tests: older versions marked `superseded_by`, `is_latest` ranking feature, "based on v2.1" and old-version warnings in `FastApi/tests/unit/pdf/test_freshness.py`
- [ ] T546 [P] [US29] Vision-reader tests: generated figure descriptions marked `generated`, used only when layout models fail in `FastApi/tests/unit/pdf/test_vision_reader.py`

### Implementation for User Story 29

- [ ] T547 [US29] Implement entity and relation extraction and graph tables in `FastApi/app/application/pdf/services/knowledge_graph.py` and a migration in `FastApi/alembic/versions/`
- [ ] T548 [P] [US29] Use the graph for query expansion and relationship answers in `FastApi/app/application/pdf/use_cases/ask_about_documents.py`
- [ ] T549 [P] [US29] Implement document and chunk quality scoring from feedback signals in `FastApi/app/application/pdf/services/document_quality.py`
- [ ] T550 [P] [US29] Surface quality problems to the owner and exclude low-quality documents from training data in `FastApi/app/adapters/inbound/rest/library.py` and `FastApi/ml/pdf_learning/synthetic_qa.py`
- [ ] T551 [P] [US29] Implement freshness, supersession and the version shown in answers in `FastApi/app/application/pdf/services/freshness.py`
- [ ] T552 [P] [US29] Implement the optional local vision-language reader (Ollama) for hard pages and figure descriptions in `FastApi/app/adapters/outbound/pdf/vision_reader.py`
- [ ] T553 [P] [US29] Evaluate optional page-image retrieval (ColPali-style) behind a flag and record the decision in `docs/adr/page-image-retrieval.md`

**Checkpoint**: The library knows relations, quality and freshness

---

## Phase 32: User Story 30 - Opt-in training from PDFs and sharing (Source: F39, F40 (sharing); READ_LEARN_FEATURE.md v2) (Priority: P30)

**Goal**: Let teams share documents under ACLs and, only with opt-in and a rights attestation, use their PDFs to improve models, with full lineage and honest limits on unlearning.

**Independent Test**: With opt-in off no derived example leaves the tenant; deleting a PDF removes its derived examples from the next dataset version; sharing with a team makes chunks retrievable only for that team.

### Tests for User Story 30 ⚠️ (write first, must FAIL)

- [ ] T554 [P] [US30] Opt-in tests: derived training examples require uploader opt-in, rights attestation, defined scope and PII scrubbing; default off in `FastApi/ml/tests/test_pdf_training_optin.py`
- [ ] T555 [P] [US30] Lineage tests: every derived example keeps `source_doc_id`; deleting a document removes its examples from future dataset versions in `FastApi/ml/tests/test_pdf_lineage.py`
- [ ] T556 [P] [US30] Sharing tests: user, team and organization ACLs enforced in the retrieval adapter, admin reads audited in `FastApi/tests/unit/pdf/test_sharing.py`
- [ ] T557 [P] [US30] Tenant isolation tests: no derived example crosses tenants when opt-in is off in `FastApi/tests/contract/test_tenant_isolation_contract.py`

### Implementation for User Story 30

- [ ] T558 [US30] Implement the opt-in and rights-attestation flow and its API in `FastApi/app/application/pdf/use_cases/training_consent.py` and `FastApi/app/adapters/inbound/rest/training_consent.py`
- [ ] T559 [P] [US30] Enforce consent, scope and PII scrubbing when building PDF training data in `FastApi/ml/pipelines/build_dataset.py`
- [ ] T560 [P] [US30] Propagate document deletion to derived examples and mark the next retrain to start from the cleaned dataset in `FastApi/app/workers/privacy_tasks.py`
- [ ] T561 [P] [US30] Implement sharing (user, team, organization) and the audited admin read in `FastApi/app/application/pdf/use_cases/share_document.py` and `FastApi/app/adapters/inbound/rest/sharing.py`
- [ ] T562 [P] [US30] Document the limits of unlearning and the isolated-adapter option for sensitive tenants in `docs/adr/pdf-training-and-unlearning.md`

**Checkpoint**: Sharing and training are consent-based, auditable and reversible where possible

---

## Phase 33: User Story 31 - Vector database foundation: registry, versioned collections, tenant/ACL isolation and the `code_knowledge` migration (Source: VECTOR_DATABASE.md sections 1, 4, 5.1, 6, 7.1, 9, 12, 13, 14; roadmap phases 1 and 2 (core)) (Priority: P31)

**Goal**: Make the existing single Qdrant collection a governed, versioned index: deterministic ids, a Postgres index registry, collection resolution by embedder version, a fail-closed tenant/ACL filter repeated in every prefetch, and a blue/green migration of the current unversioned `code_knowledge`.

**Independent Test**: On a real Qdrant, a chunk owned by `user:alice` is never returned to `user:bob` or to another tenant by a hybrid query; upserting the same chunk id twice leaves one point; a query vector from embedder `emb_v1` only ever reaches the collection built with `emb_v1`; a service started against a collection with a different `embedder_version`, or with a filtered field lacking a payload index, refuses to become ready; the legacy collection is migrated with zero failed queries.

### Tests for User Story 31 ⚠️ (write first, must FAIL)

- [ ] T563 [P] [US31] Unit tests: `point_id` is a deterministic UUIDv5 of the canonical id; `collection_name`/`parse_collection_name` round-trip and reject bad names; the namespace constant is frozen in `FastApi/tests/unit/vector/test_ids_and_names.py`
- [ ] T564 [P] [US31] Unit tests: `Scope` and `mandatory_filter` fail closed without tenant or subjects, never read subjects from request bodies, honor `doc_ids` and `latest_only` in `FastApi/tests/unit/vector/test_scope.py`
- [ ] T565 [P] [US31] Unit tests: taxonomy validation rejects unknown `framework`, `artifact_type`, `language`, `chunk_type` and `source_type` values and maps legacy `spring` to a reviewed value in `FastApi/tests/unit/vector/test_taxonomy.py`
- [ ] T566 [P] [US31] Unit tests: `resolve_collection` picks the live collection for the query's embedder version and fails loudly with zero or two live rows; registry status moves only building→verifying→shadow→live→retired; the live flip is one transaction in `FastApi/tests/unit/vector/test_resolution.py`
- [ ] T567 [P] [US31] Unit tests: the Qdrant filter builder repeats the mandatory filter inside every `Prefetch` and never relies on the top-level filter; alias switch is one request with two actions in `FastApi/tests/unit/vector/test_qdrant_filters.py`
- [ ] T568 [P] [US31] Unit tests: startup guards refuse an `embedder_version` mismatch, a missing payload index for any filtered field, and a missing live registry row in `FastApi/tests/unit/vector/test_startup_guards.py`
- [ ] T569 [P] [US31] Contract suite for the new `PointWriter`, `PointSearcher` and `CollectionAdmin` ports (scores sorted descending, `limit` honored, idempotent upsert, delete by filter, documented replace-on-upsert behavior) run against the in-memory fake and Qdrant in `FastApi/tests/contract/test_point_store_contract.py`
- [ ] T570 [P] [US31] Contract suite for `IndexRegistry` and `TaxonomyRepository` run against the in-memory fake and a Postgres container in `FastApi/tests/contract/test_index_registry_contract.py`
- [ ] T571 [P] [US31] Real-server integration tests (testcontainers): tenant and ACL isolation under hybrid query, same-id upsert leaves one point, re-upsert with only `dense` empties `sparse`, delete of one document version, a concurrent reader never fails while the alias switches in `FastApi/tests/integration/vector/test_qdrant_platform.py`
- [ ] T572 [P] [US31] Real-server tests for every item marked **verify** in VECTOR_DATABASE.md (filter inside `prefetch`, batch `set_payload`, `hnsw_ef`, `exact`, `score_threshold`, `with_payload` include, RRF form, `wait=true`) and a record of the results in `FastApi/tests/integration/vector/test_qdrant_api_assumptions.py`
- [ ] T573 [P] [US31] ANN recall gate test: golden queries with `exact: true` as ground truth versus approximate search stay above the floor, and the payload-index assertion reads collection info in `FastApi/tests/integration/vector/test_ann_recall.py`
- [ ] T574 [P] [US31] Blue/green tests: dual-write while building, resumable keyset backfill, point counts equal `points_expected`, promote in one transaction, rollback by registry change in `FastApi/tests/integration/vector/test_blue_green.py`
- [ ] T575 [P] [US31] Compatibility test: the US2 contract, recall and API suites (`test_vector_store_contract.py`, `test_qdrant_store.py`, `test_retrieval_recall.py`, `test_questions_retrieval_api.py`) pass unchanged on the refactored store in `FastApi/tests/integration/test_qdrant_store.py`

### Implementation for User Story 31

- [ ] T576 [P] [US31] Create the pure domain package: `point_id`, `collection_name`/`parse_collection_name`, `Scope`, `mandatory_filter` spec, taxonomy enums and registry row/status types in `FastApi/app/domain/vector/` (no framework imports)
- [ ] T577 [P] [US31] Create the application ports `PointWriter`, `PointSearcher`, `CollectionAdmin`, `IndexRegistry` and `TaxonomyRepository` (small, segregated) in `FastApi/app/application/ports/vector_index.py`, `FastApi/app/application/ports/index_registry.py` and `FastApi/app/application/ports/taxonomy_repository.py`
- [ ] T578 [P] [US31] Implement the in-memory fakes for the new ports (same contract tests) in `FastApi/tests/fakes/vector_index.py`
- [ ] T579 [P] [US31] Add `VectorSettings` (embedder version, schema version, `memory`-tier vs legacy flags, API key and read-only key, TLS, tenant default, thresholds) with `VECTOR__` env nesting and secret-safe repr in `FastApi/app/config.py`
- [ ] T580 [P] [US31] Add Alembic migrations `0002_index_registry` and `0003_taxonomy` (seeded with the starting vocabularies) and the SQL adapters in `FastApi/alembic/versions/` and `FastApi/app/adapters/outbound/postgres/index_registry.py`, `FastApi/app/adapters/outbound/postgres/taxonomy.py`
- [ ] T581 [US31] Implement collection specifications and creation in the safe order (create with `metadata`, create all payload indexes, then load) with version-aware memory settings (`memory` tiers on 1.19+, `on_disk`/`always_ram` before) in `FastApi/app/adapters/outbound/qdrant/collection_specs.py` and `FastApi/app/adapters/outbound/qdrant/admin.py`
- [ ] T582 [P] [US31] Implement the server capability probe (version, features) used to pick settings and to skip unsupported features with a clear log in `FastApi/app/adapters/outbound/qdrant/capabilities.py`
- [ ] T583 [P] [US31] Implement the Qdrant filter builder (mandatory filter in every `Prefetch`, `is_tenant` index on `tenant_id`) in `FastApi/app/adapters/outbound/qdrant/filters.py`
- [ ] T584 [US31] Implement `QdrantPointStore` (upsert with batches of 64–256, `wait=True` on the last batch, `set_payload` for payload-only changes, delete by filter, hybrid RRF, nearest with `score_threshold`) in `FastApi/app/adapters/outbound/qdrant/point_store.py`
- [ ] T585 [P] [US31] Extract the BM25-style sparse encoder from `qdrant_vector_store.py` into `FastApi/app/adapters/outbound/qdrant/sparse_encoder.py` and keep the sparse vector named `sparse` in the new layout (schema 1)
- [ ] T586 [US31] Refactor `QdrantVectorStore` into a thin adapter over `QdrantPointStore` so `VectorWriter`/`VectorSearcher` and all US2 callers keep working in `FastApi/app/adapters/outbound/qdrant/qdrant_vector_store.py`
- [ ] T587 [US31] Extend the chunk payload to the full `code_knowledge` schema (tenant, ACL, doc, version, `is_latest`, `chunk_type`, `natural_language`, provenance, versions) as a validated Pydantic model at the adapter boundary in `FastApi/app/application/vector/chunk_payload.py`
- [ ] T588 [US31] Derive `Scope` from the verified JWT claims (never the body) with a single-tenant default for local mode in `FastApi/app/adapters/inbound/rest/scope.py` and pass it through `AskQuestion` retrieval
- [ ] T589 [US31] Implement `ResolveCollection` and the startup guards (embedder metadata check, payload-index assertion, live registry row) in `FastApi/app/application/vector/resolve_collection.py` and `FastApi/app/application/vector/guards.py`; add the result to `/health/ready`
- [ ] T590 [US31] Wire the registry, resolver and API-key-aware Qdrant client in the composition root (fail closed when configured and unreachable) in `FastApi/app/bootstrap.py` and `FastApi/app/container.py`
- [ ] T591 [US31] Implement the index admin CLI (create, list, verify, promote, rollback, alias switch, snapshot) in `FastApi/scripts/index_admin.py`; this is the CLI named by T247
- [ ] T592 [US31] Implement the blue/green use cases (`BuildIndex`, `Backfill` keyset-paginated and resumable, `VerifyIndex`, `PromoteIndex` in one transaction, `RollbackIndex`) in `FastApi/app/application/vector/blue_green.py`
- [ ] T593 [US31] Implement the one-off migration of the legacy unversioned `code_knowledge` (vector `bm25`) to `code_knowledge__<embedder>__s1` and record it in the registry in `FastApi/scripts/migrate_legacy_collection.py`
- [ ] T594 [P] [US31] Pin the Qdrant image (replace `qdrant/qdrant:latest`), enable the API key and read-only key, and set the snapshot storage to MinIO in `FastApi/deploy/docker/docker-compose.yml`
- [ ] T595 [US31] Add the Qdrant production manifests (3-node StatefulSet with anti-affinity, PodDisruptionBudget `maxUnavailable: 1`, probes, Secrets, `NetworkPolicy` that only the api, ingestion and training pods reach 6333/6334 and only Qdrant pods reach 6335, non-root, read-only root filesystem) in `FastApi/deploy/k8s/base/qdrant/` (extends T167)
- [ ] T596 [US31] Add the snapshot job (per node, to MinIO, 7 daily and 4 weekly, taken before every promotion), the restore-into-staging drill script and the alias-map restore from the registry in `FastApi/scripts/qdrant_snapshot.py` and `FastApi/deploy/k8s/base/qdrant/snapshot-cronjob.yaml`
- [ ] T597 [P] [US31] Add Prometheus scrape config and alert rules (points versus `points_expected`, indexed versus total vectors, p95 latency, disk above 80%, collection without a live row, replicas out of sync) in `FastApi/deploy/k8s/observability/alerts/qdrant.yaml` and a Grafana dashboard `FastApi/deploy/k8s/observability/dashboards/qdrant.json`
- [ ] T598 [US31] Validate the new manifests with kubeconform and record the Qdrant version notes (memory tiers, `metadata`, RRF parameters) in `FastApi/deploy/k8s/README.md`
- [ ] T599 [P] [US31] Write the ADR for the vector layout (one collection per purpose and embedder, shared tenant collection, resolution rule, Postgres as system of record) and the runbook (rebuild time, restore drill, retirement window) in `docs/adr/` and `docs/vector-runbook.md`

**Checkpoint**: the platform can rebuild, migrate and roll back its index without downtime, and no query can cross a tenant or ACL boundary

---

## Phase 34: User Story 32 - Template routing, semantic cache and glossary lookup on Qdrant (Source: VECTOR_DATABASE.md sections 5.3, 5.4, 5.5, 7.2, 7.3, 7.6; roadmap phases 2 and 3 (glossary)) (Priority: P32)

**Goal**: Add the retrieval-side collections that make answers faster and more precise: `templates` for template-first routing, `semantic_cache` for repeated questions (answer bodies stay in Redis), and `glossary_terms` for semantic term lookup.

**Independent Test**: A request such as "create a REST controller for User" routes to its template through the `templates` index when rules are unsure; a repeated question is answered from the cache only for a caller with the same `scope_hash`; a user who cannot read a document never receives a cached answer built from it; "dispatcher servlet" resolves to `DispatcherServlet` through the glossary index.

### Tests for User Story 32 ⚠️ (write first, must FAIL)

- [ ] T600 [P] [US32] Template routing tests: group hits by `template_id` and take the best score, filter `status=active`, `framework`, `language`, below-threshold falls back to retrieval, ASR-noisy utterances ("controler") still route in `FastApi/tests/unit/vector/test_template_router.py`
- [ ] T601 [P] [US32] Cache safety tests: `scope_hash` is the SHA-256 of tenant, sorted subjects and document scope; a different scope never hits; only gate `answer` is stored; `prompt_version` or `index_version` change misses; expired entries are ignored in `FastApi/tests/unit/vector/test_semantic_cache.py`
- [ ] T602 [P] [US32] Cache invalidation tests: updating or deleting a document removes entries whose `depends_on_doc_ids` contain it, and the expiry sweep deletes by `expires_at` in `FastApi/tests/unit/vector/test_cache_invalidation.py`
- [ ] T603 [P] [US32] Cache threshold test: a labelled set of question pairs that should and should not share an answer tunes the 0.95 default in `FastApi/ml/tests/test_cache_threshold.py` with data in `FastApi/ml/evaluation/cache_pairs.jsonl`
- [ ] T604 [P] [US32] Glossary lookup tests: approved terms only, scope `global`/`tenant`/`user`, "dispatcher servlet" finds `DispatcherServlet`, near-duplicate candidates are flagged for review in `FastApi/tests/unit/vector/test_glossary_index.py`
- [ ] T605 [P] [US32] Real-server tests for the three collections (specs, indexes, filters, `score_threshold`, delete by filter) in `FastApi/tests/integration/vector/test_secondary_collections.py`

### Implementation for User Story 32

- [ ] T606 [US32] Add the collection specs and payload indexes for `templates`, `semantic_cache` and `glossary_terms` and create them through the registry in `FastApi/app/adapters/outbound/qdrant/collection_specs.py`
- [ ] T607 [P] [US32] Create the `TemplateIndex` port and the Qdrant adapter (best score per `template_id`, status and compatibility filters) in `FastApi/app/application/ports/template_index.py` and `FastApi/app/adapters/outbound/qdrant/template_index.py`
- [ ] T608 [P] [US32] Implement the template sync use case that indexes 20–50 paraphrases per template (including ASR-noisy ones) from the template registry files, idempotent by `example_id`, in `FastApi/app/application/vector/index_templates.py` (the template registry itself is defined by the template-responses work and is read through a port)
- [ ] T609 [US32] Implement the Qdrant-backed `SemanticCache` (question vector in Qdrant, answer body in Redis under `answer_ref`, TTL, tunable threshold) behind the existing cache port in `FastApi/app/adapters/outbound/cache/qdrant_semantic_cache.py`; this is the implementation T248 decorates
- [ ] T610 [US32] Implement cache invalidation on document update and delete (`depends_on_doc_ids`) and hook it into the deletion saga in `FastApi/app/application/vector/cache_invalidation.py`
- [ ] T611 [US32] Add the Celery beat task that sweeps expired cache entries every few minutes in `FastApi/app/workers/vector_tasks.py`
- [ ] T612 [US32] Implement the `GlossaryIndex` adapter and the sync from the Postgres glossary (approved and pending terms only) with the `stt_hotword` export for the Whisper prompt in `FastApi/app/adapters/outbound/qdrant/glossary_index.py` and `FastApi/app/application/vector/sync_glossary.py`
- [ ] T613 [US32] Add cache hit-rate, saved-latency and stale-hit metrics and a dashboard panel in `FastApi/app/adapters/outbound/observability/vector_metrics.py` and `FastApi/deploy/k8s/observability/dashboards/qdrant.json`
- [ ] T614 [US32] Wire the three indexes and the cache decorator into the composition root behind settings (off by default) in `FastApi/app/bootstrap.py`

**Checkpoint**: template routing and caching can be switched on per environment without any cross-scope leak

---

## Phase 35: User Story 33 - Training-data hygiene, automated re-embedding and scale-out on Qdrant (Source: VECTOR_DATABASE.md sections 5.2, 5.6, 5.7, 7.4, 7.5, 8, 9 (JWT roles), 11, 14; roadmap phases 3 to 5) (Priority: P33)

**Goal**: Use the vector database to keep training data clean (duplicates, leakage, label noise, drift), mine hard negatives, re-embed every collection automatically after an embedder change with shadow and canary rollout, and scale to a replicated cluster with least-privilege tokens.

**Independent Test**: A near-duplicate or leaked test utterance fails the CI data test; hard negatives for a query exclude its known positive; promoting embedder `emb_v2` builds, verifies and shadows every `emb_v2` collection while old pods keep answering from `emb_v1`; a read-only token cannot write; deleting a user's consent removes their `utterances` and `user_memory` points.

### Tests for User Story 33 ⚠️ (write first, must FAIL)

- [ ] T615 [P] [US33] Hygiene tests: near-duplicate groups, leakage of golden/test items against `split=train`, label-noise by 10-neighbour vote, kNN intent fallback only from `label_status=gold` in `FastApi/ml/tests/test_vector_hygiene.py`
- [ ] T616 [P] [US33] Hard-negative tests: ranks 5 to 30, known positives excluded by `has_id`, only tenants with training consent, false negatives dropped by rule in `FastApi/ml/tests/test_hard_negatives_vector.py`
- [ ] T617 [P] [US33] Round-trip tests: a synthetic question is kept only when its source chunk is in the top 5, and the retrieval-gap report lists the rest in `FastApi/ml/tests/test_round_trip_filter.py`
- [ ] T618 [P] [US33] Drift tests: weekly mean nearest-neighbour similarity, share under 0.6 and centroid shift against a reference week raise the alarm in `FastApi/ml/tests/test_vector_drift.py`
- [ ] T619 [P] [US33] Lineage and consent tests: delete by `doc_id`, `source_doc_id`, `depends_on_doc_ids` and `user_hash` removes derived points in every collection, and consent withdrawal purges `utterances` and `user_memory` in `FastApi/tests/integration/vector/test_lineage_deletion.py`
- [ ] T620 [P] [US33] Rollout tests: pods with embedder `emb_v2` resolve the `emb_v2` collections while `emb_v1` pods resolve theirs; shadow replay compares overlap; rollback is one registry change in `FastApi/tests/integration/vector/test_embedder_rollout.py`
- [ ] T621 [P] [US33] Security tests: a read-only token cannot write, claims match physical names or aliases as proven against the real server, and the training identity sees only consenting tenants in `FastApi/tests/integration/vector/test_roles.py`
- [ ] T622 [P] [US33] Cluster failure drill test plan (node loss, snapshot restore, rollback) as a script-driven check in `FastApi/tests/integration/vector/test_cluster_drill.py` (skipped unless a cluster is available)

### Implementation for User Story 33

- [ ] T623 [P] [US33] Add the `utterances` collection spec (tenant index on `tenant_id` and `user_hash`, consent flags, split and label status indexes) and the loader that mirrors dataset builds from DVC and Postgres in `FastApi/ml/vector/utterance_index.py`
- [ ] T624 [US33] Implement dedupe, leakage check, label-noise detection and active-learning sampling (clustering job sets `cluster_id`) in `FastApi/ml/vector/hygiene.py` and add the leakage check to the CI data tests in `FastApi/ml/evaluation/expectations/`
- [ ] T625 [US33] Implement the kNN intent vote as an optional second opinion for the confidence gate behind a flag in `FastApi/app/adapters/outbound/qdrant/knn_intent.py`
- [ ] T626 [US33] Implement hard-negative mining and the round-trip filter on top of the Qdrant adapter and plug them into the existing training code in `FastApi/ml/training/embedder/hard_negatives.py` (T295) and `FastApi/ml/pdf_learning/round_trip.py`
- [ ] T627 [P] [US33] Implement the weekly drift job and publish its metrics to the existing drift alarms in `FastApi/ml/pipelines/vector_drift.py`
- [ ] T628 [US33] Automate the full cycle (reindex every purpose for a new embedder, verify gates, shadow, canary by embedder version, promote or roll back) as a Celery/Argo workflow with a human approval step in `FastApi/ml/pipelines/reindex_all.py`
- [ ] T629 [US33] Implement the shadow replay of sampled live queries against the candidate collections and the overlap report in `FastApi/ml/pipelines/shadow_replay.py`
- [ ] T630 [US33] Implement lineage deletion across all collections and consent-withdrawal purge in `FastApi/app/application/vector/lineage_delete.py` and expose it to the deletion saga (US20) and the consent flow (US30)
- [ ] T631 [US33] Add JWT RBAC roles (retrieval `r`, ingestion `rw`, training read-only) and TLS to the Qdrant config and clients, with token rotation by `alt_api_key` in `FastApi/deploy/k8s/base/qdrant/config.yaml` and `FastApi/app/adapters/outbound/qdrant/auth.py`
- [ ] T632 [P] [US33] Add the opt-in `user_memory` collection (per-user tenant index, consent, PII-scrubbed text, retention, delete by `user_hash`) behind a flag in `FastApi/app/adapters/outbound/qdrant/user_memory.py`
- [ ] T633 [P] [US33] Evaluate the optional `page_regions` multivector collection (`max_sim`) behind a flag and record the decision (extends T553) in `docs/adr/`
- [ ] T634 [P] [US33] Decide shard count and replication for production from measured data volume and record sizing with the `estimate_gb` helper in `FastApi/scripts/vector_sizing.py` and `docs/vector-runbook.md`
- [ ] T635 [P] [US33] Record default answers to the VECTOR_DATABASE.md open questions (embedder and dimension, tenants, self-hosted Qdrant, pinned version, retention, global templates, BM25 vs learned sparse) in `specs/001-voice-dev-assistant/spec.md`

**Checkpoint**: an embedder change is a rehearsed, reversible operation and training data is deduplicated, leak-free and deletable by lineage

---

## Phase 36: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

- [ ] T636 [P] Write ADRs (STT placement, Qdrant, single deployable vs microservices) in `docs/adr/`
- [ ] T637 [P] Write `specs/001-voice-dev-assistant/quickstart.md` (Compose up, seed, ask)
- [ ] T638 Verify ≥ 80% coverage on domain/application and fix gaps in `FastApi/tests/`
- [ ] T639 [P] Accessibility pass (WCAG 2.2 AA, TalkBack, VoiceOver) across clients
- [ ] T640 [P] Security review (dependency, SAST, secret scan, IaC scan) and remediation
- [ ] T641 [P] Add Playwright visual-regression snapshots of Idle/Listening/Answer in light and dark, compared with the design references, in `Angular/e2e/visual.spec.ts`
- [ ] T642 [P] Design QA: compare each implemented screen with `UX/UI /angular.html`, `UX/UI /android.html`, `UX/UI /ios.html` (spacing, 44px touch targets, radii, tokens) and log deviations in `specs/001-voice-dev-assistant/design-notes.md`
- [ ] T643 [P] Write the ML runbook (data refresh, retrain, shadow/canary, rollback, drift response) in `docs/ml-runbook.md`
- [ ] T644 [P] Review ML pipelines for PII leakage, consent enforcement, poisoning safeguards (rate limits, per-user caps, rare-class confirmation) and model-collapse protection in `docs/adr/ml-safeguards.md`
- [ ] T645 [P] Record the ML gate floors as placeholders to be replaced by measured baselines in `FastApi/ml/evaluation/gates.yaml`
- [ ] T646 [P] Write the PDF ingestion runbook (reprocessing, dead-letter handling, quarantine review, quota changes, rollback) in `docs/pdf-runbook.md`
- [ ] T647 [P] Review the PDF pipeline for sandbox escapes, cross-user retrieval, prompt injection through documents and rights/consent handling, and record findings in `docs/adr/pdf-security.md`
- [ ] T648 [P] Record the default answers to the PDF open questions (private per user in the MVP, English first, copy-protected files only after rights attestation, training off by default, offline = library and summaries only) in `docs/adr/pdf-open-questions.md`
- [ ] T649 Run quickstart validation end to end and record results in `specs/001-voice-dev-assistant/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup; BLOCKS all user stories
- **User Stories (Phase 3–35)**: depend on Foundational; then proceed in priority order or in parallel
- **Polish (Phase 33)**: depends on the stories being delivered

### User Story Dependencies

- **US1 (P1)**: starts after Foundational; no story dependencies
- **US2 (P2)**: after Foundational; extends `AskQuestion` from US1 (T076 needs T043)
- **US3 (P3)**: needs the model from US10 (or a fake/baseline classifier) and, for retrieval filters, US2 (T088 needs T076)
- **US4 (P4)**: after US2 (needs retrieved chunks); independent of US3
- **US5 (P5)**: needs the OpenAPI contract from US1 and the design tokens (Phase 2); can run in parallel with US2–US4
- **US6 (P6)**: needs US1/US5 clients for the feedback UI; no model dependency
- **US7 (P7)**: needs US1/US5 screens, US6 feedback and the US1 OpenAPI contract; backend tasks can start after Foundational
- **US9 (P9)**: after Foundational; independent of the clients; should run before US3 and US10
- **US10 (P10)**: needs US9 datasets, harness and baseline; feeds US3
- **US11 (P11)**: needs US2 (retrieval) and US4 (generation); STT gates need US9 harness
- **US12 (P12)**: needs US6 (feedback storage), US10 (confidence/versions) and US11 (pipeline stages to trace)
- **US13 (P13)**: needs US12 (reviewed data), US11 (versioned index) and US8 manifests for GPU Jobs
- **US14 (P14)**: optional; only after measured gaps from US10–US13
- **US16 (P16)**: needs Foundational, US2 (Qdrant, ingestion) and US8 manifests for the workers; independent of the ML track
- **US17 (P17)**: needs Foundational; start it together with US16 so the parsers are written against the golden corpus
- **US18 (P18)**: needs US16 (pipeline, ports) and US17 (corpus and gates)
- **US19 (P19)**: needs US18 (blocks) and US2 (index); reuses the versioned index from US11
- **US20 (P20)**: needs US19, US11 (grounded generation, guardrails) and US10 (confidence gate)
- **US21 (P21)**: needs US16 and US20 APIs and the design tokens; Android, iOS and web are independent
- **US22 (P22)**: needs US18; adds the `gpu` queue workloads
- **US23 (P23)**: needs US19 and US22 (tables); uses US11 hybrid retrieval
- **US24 (P24)**: needs US19 and the `learn` queue
- **US25 (P25)**: needs US19, US10/US12 (taxonomy, review queue) and US24
- **US26 (P26)**: needs US21 and US24
- **US27 (P27)**: needs US19 and US17 (golden gates)
- **US28 (P28)**: needs US23 and US27 (versions)
- **US29 (P29)**: needs US20, US12 (feedback signals) and US27
- **US30 (P30)**: needs US25, US13 (dataset versioning) and US20
- **US31 (P31)**: needs US2 (current Qdrant adapter) and US16 (Postgres and Alembic); do it before US19 so the PDF index is built on the versioned store (T421, T422, T434, T489 reuse it); it owns T247
- **US32 (P32)**: needs US31 and US11 (cache decorator, guardrails); glossary sync needs US25; template sync needs the template registry from the template-responses work
- **US33 (P33)**: needs US31, US32, US13 (training pipeline) and US20 (deletion saga); cluster and JWT tasks need US8 manifests
- **US15 (P15)**: needs the OpenAPI contract (US1 onwards); can start right after US2 and grows as endpoints land (the flows for US6, US7 and US12 are separate tasks)
- **US8 (P8)**: manifests can start once images exist; final validation after US1–US7

### Within Each User Story

- Tests first and failing → ports → fakes → use cases → adapters → endpoints/UI → wiring
- Commit after each task or logical group (Conventional Commits)

### Parallel Opportunities

- All Setup tasks marked [P]; most Foundational [P] tasks after T014/T015
- Within a story, all tests [P] and independent ports/adapters [P]
- US5 (mobile) can proceed in parallel with US2–US4 once the contract exists

---

## Parallel Example: User Story 1

```text
# Tests together:
Task: "Unit test AskQuestion in FastApi/tests/unit/application/test_ask_question.py"
Task: "Contract test Transcriber in FastApi/tests/contract/test_transcriber_contract.py"
Task: "Component test voice-capture in Angular/src/app/voice-capture/voice-capture.component.spec.ts"

# Then independent implementation:
Task: "FasterWhisperTranscriber in FastApi/app/adapters/outbound/stt/faster_whisper_transcriber.py"
Task: "AudioRecorderService in Angular/src/app/voice-capture/audio-recorder.service.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup → 2. Phase 2 Foundational → 3. Phase 3 US1
4. STOP and VALIDATE with the independent test; demo

### Incremental Delivery

1. Setup + Foundational → 2. US1 (MVP) → 3. US2 → 4. US3 → 5. US4 → 6. US5 → 7. US6 → 8. US7 → 9. US8 → 10. ML track US9 → US10 → US11 → US12 → US13 (US14 optional); US9–US10 can start right after Foundational and run in parallel with US1–US2
Each story adds value without breaking the previous ones.

### Parallel Team Strategy

After Foundational: Dev A backend US1→US2→US3, Dev B Angular + US5 Android, Dev C iOS + US7 infrastructure.

---

## Notes

- [P] tasks touch different files with no dependencies
- Verify tests fail before implementing; keep domain free of framework imports (import-linter)
- Pin latest stable versions at scaffold time; secrets only via environment/secret manager
