---

description: "Task list for Voice-Driven Developer Assistant"
---

# Tasks: Voice-Driven Developer Assistant

**Input**: Design documents from `/specs/001-voice-dev-assistant/`

**Prerequisites**: plan.md (required), spec.md (required for user stories); source: `FEATURE.md`

**Tests**: INCLUDED. TDD is mandatory (constitution Principle I; FEATURE.md section 6). In every
story, write the tests first and confirm they FAIL before implementing.

**Status note**: Tasks marked `[X]` for `FastApi/` were verified (tests, ruff, mypy, import-linter, Docker build). `[X]` tasks for `Angular/`, `Android/` and `IOS/` (except the iOS theme test, which ran via `swift test`) are written but NOT built or tested on this machine (no Node/Gradle/Android SDK). US2 backend tasks (T061–T079) and the US9 data/evaluation tasks (T179–T206) were verified except the real Piper/ffmpeg/Whisper adapters, the TensorFlow `tf.data` builder and DVC (none installed here); the Angular sources panel (T080–T081) is written but unverified. T029 and T030 stay open (see notes in the completion report).

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

- [ ] T082 [P] [US3] Contract test suite for `IntentClassifier` in `FastApi/tests/contract/test_intent_classifier_contract.py`
- [ ] T083 [P] [US3] Golden-set accuracy test (threshold from env) in `FastApi/tests/ml/test_intent_golden_set.py`
- [ ] T084 [P] [US3] Unit test low-confidence fallback to `FIND_DOCS` in `FastApi/tests/unit/application/test_intent_fallback.py`

### Implementation for User Story 3

- [ ] T085 [P] [US3] Define `IntentClassifier` port in `FastApi/app/application/ports/intent_classifier.py`
- [ ] T086 [US3] Implement `TFServingIntentClassifier` adapter (gRPC/REST) in `FastApi/app/adapters/outbound/intent/tf_serving_classifier.py`
- [ ] T087 [P] [US3] Implement `FakeClassifier` in `FastApi/tests/fakes/`
- [ ] T088 [US3] Wire intent into `AskQuestion` (entities → search filters, confidence fallback) in `FastApi/app/application/use_cases/ask_question.py`
- [ ] T089 [P] [US3] Add TF Serving container to `FastApi/deploy/docker/docker-compose.yml` and `FastApi/deploy/docker/tf-serving.Dockerfile`
- [ ] T090 [US3] Add golden-set gate job to `.github/workflows/backend.yml`

**Checkpoint**: Intent-aware retrieval works and is guarded by CI

---

## Phase 6: User Story 4 - Generated answers with graceful degradation (Priority: P4)

**Goal**: Ollama-generated answers with a circuit breaker and retrieval-only fallback.

**Independent Test**: With Ollama stopped, questions still return snippet answers.

### Tests for User Story 4 ⚠️

- [ ] T091 [P] [US4] Unit tests for `CircuitBreakerGenerator` states (closed/open/half-open) in `FastApi/tests/unit/adapters/test_circuit_breaker_generator.py`
- [ ] T092 [P] [US4] Unit tests for `AnswerBuilder` (text, sources, confidence, snippets) in `FastApi/tests/unit/application/test_answer_builder.py`
- [ ] T093 [P] [US4] Integration test fallback when LLM is down in `FastApi/tests/integration/test_llm_fallback.py`

### Implementation for User Story 4

- [ ] T094 [P] [US4] Implement `AnswerBuilder` in `FastApi/app/application/services/answer_builder.py`
- [ ] T095 [P] [US4] Implement `SnippetAnswerGenerator` (retrieval-only) in `FastApi/app/adapters/outbound/answer/snippet_answer_generator.py`
- [ ] T096 [P] [US4] Implement `OllamaAnswerGenerator` with RAG prompt template and timeouts in `FastApi/app/adapters/outbound/answer/ollama_answer_generator.py`
- [ ] T097 [US4] Implement `CircuitBreakerGenerator` decorator with fallback in `FastApi/app/adapters/outbound/answer/circuit_breaker_generator.py`
- [ ] T098 [US4] Wire generators in the composition root and add LLM settings in `FastApi/app/main.py` and `FastApi/app/config.py`
- [ ] T099 [P] [US4] Add `AnswerDelivered` domain event and in-process event bus in `FastApi/app/application/events.py`

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

- [ ] T207 [P] [US10] Model tests: joint model outputs `intent` and `slots` logits (linear outputs, masked padding) in `FastApi/ml/tests/test_intent_model.py`
- [ ] T208 [P] [US10] Calibration tests: `fit_temperature` lowers ECE on held-out logits and is fitted only on validation data in `FastApi/ml/tests/test_calibration.py`
- [ ] T209 [P] [US10] OOD tests: `OUT_OF_SCOPE` hard negatives ("how do I use a game controller") are rejected via class, calibrated threshold and retrieval-score threshold in `FastApi/ml/tests/test_out_of_scope.py`
- [ ] T210 [P] [US10] Export tests: SavedModel exported to a numbered version directory with serving signature and temperature file in `FastApi/ml/tests/test_export.py`
- [ ] T211 [P] [US10] Registry tests: registration is refused when git SHA, image digest, dataset hash, seeds, hyperparameters or metrics are missing in `FastApi/ml/tests/test_registry.py`
- [ ] T212 [P] [US10] Unit tests for `ConfidenceGate` (answer / clarify / abstain, missing required `LANGUAGE`, `OUT_OF_SCOPE`) in `FastApi/tests/unit/domain/test_confidence_gate.py`
- [ ] T213 [P] [US10] Unit tests for `IntentRouter` (handler registry, fallback, no retrieval for `META_COMMAND`) in `FastApi/tests/unit/application/test_intent_router.py`
- [ ] T214 [P] [US10] Latency test: intent inference stays inside its CI budget in `FastApi/ml/tests/test_intent_latency.py`
- [ ] T215 [P] [US10] Replace the placeholder golden-set test with real gate evaluation against `FastApi/ml/data/golden/` in `FastApi/tests/ml/test_intent_golden_set.py`

### Implementation for User Story 10

- [ ] T216 [US10] Implement `build_joint_model` (BiLSTM, two linear-logit heads) in `FastApi/ml/training/intent/model.py`
- [ ] T217 [US10] Implement training (class weights, loss weights 1.0/0.5, EarlyStopping, per-epoch checkpoints, fixed seeds, optional `mixed_float16`, MLflow logging) in `FastApi/ml/training/intent/train.py`
- [ ] T218 [P] [US10] Implement temperature-scaling calibration (`fit_temperature`) in `FastApi/ml/training/intent/calibrate.py`
- [ ] T219 [P] [US10] Implement intent/slot evaluation (macro-F1, slot F1, OOD recall, ECE, slices) writing `metrics.json` in `FastApi/ml/evaluation/intent_eval.py`
- [ ] T220 [P] [US10] Implement SavedModel export to `artifacts/intent/<version>/` with `temperature.json` in `FastApi/ml/training/intent/export.py`
- [ ] T221 [P] [US10] Implement model registration to the MLflow Registry with run metadata and model card generation in `FastApi/ml/registry/register.py` and `FastApi/ml/registry/model_card.md`
- [ ] T222 [P] [US10] Create the training container image (CPU default, GPU build arg) in `FastApi/deploy/docker/ml-train.Dockerfile`
- [ ] T223 [P] [US10] Configure TF Serving multi-version model config (candidate and champion side by side) in `FastApi/deploy/docker/tf-serving/models.config`
- [ ] T224 [US10] Update `TFServingIntentClassifier` to apply the stored temperature and decode BIO tags into entities in `FastApi/app/adapters/outbound/intent/tf_serving_classifier.py`
- [ ] T225 [US10] Implement `ConfidenceGate` policy (calibrated thresholds 0.80 / 0.50, required entities per intent) in the domain in `FastApi/app/domain/confidence_gate.py`
- [ ] T226 [US10] Implement `IntentRouter` with handler registry and fallback in `FastApi/app/application/services/intent_router.py`
- [ ] T227 [US10] Apply profile default entities before the gate and return `status=clarify` with option chips or `status=abstain` in `FastApi/app/application/use_cases/ask_question.py`
- [ ] T228 [P] [US10] Update OpenAPI for `clarify`/`abstain` response variants and regenerate clients in `FastApi/api-contracts/openapi.yaml`
- [ ] T229 [P] [US10] Add the intent metric gates (macro-F1, slot F1, OOD recall, ECE, slice regression) to `.github/workflows/ml.yml`

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
- [ ] T247 [US11] Implement versioned collections (`code_knowledge_vN`), alias switch/rollback and `embedder_version` guard in `FastApi/app/adapters/outbound/qdrant/versioned_index.py` and CLI `FastApi/scripts/index_admin.py`
- [ ] T248 [P] [US11] Implement `SemanticCache` decorator (Redis vector search, threshold 0.95 tunable) in `FastApi/app/adapters/outbound/cache/semantic_cache.py`
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

## Phase 17: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

- [ ] T317 [P] Write ADRs (STT placement, Qdrant, single deployable vs microservices) in `docs/adr/`
- [ ] T318 [P] Write `specs/001-voice-dev-assistant/quickstart.md` (Compose up, seed, ask)
- [ ] T319 Verify ≥ 80% coverage on domain/application and fix gaps in `FastApi/tests/`
- [ ] T320 [P] Accessibility pass (WCAG 2.2 AA, TalkBack, VoiceOver) across clients
- [ ] T321 [P] Security review (dependency, SAST, secret scan, IaC scan) and remediation
- [ ] T322 [P] Add Playwright visual-regression snapshots of Idle/Listening/Answer in light and dark, compared with the design references, in `Angular/e2e/visual.spec.ts`
- [ ] T323 [P] Design QA: compare each implemented screen with `UX/UI /angular.html`, `UX/UI /android.html`, `UX/UI /ios.html` (spacing, 44px touch targets, radii, tokens) and log deviations in `specs/001-voice-dev-assistant/design-notes.md`
- [ ] T324 [P] Write the ML runbook (data refresh, retrain, shadow/canary, rollback, drift response) in `docs/ml-runbook.md`
- [ ] T325 [P] Review ML pipelines for PII leakage, consent enforcement, poisoning safeguards (rate limits, per-user caps, rare-class confirmation) and model-collapse protection in `docs/adr/ml-safeguards.md`
- [ ] T326 [P] Record the ML gate floors as placeholders to be replaced by measured baselines in `FastApi/ml/evaluation/gates.yaml`
- [ ] T327 Run quickstart validation end to end and record results in `specs/001-voice-dev-assistant/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup; BLOCKS all user stories
- **User Stories (Phase 3–16)**: depend on Foundational; then proceed in priority order or in parallel
- **Polish (Phase 17)**: depends on the stories being delivered

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
