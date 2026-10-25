# Implementation Plan: Voice-Driven Developer Assistant

**Branch**: `001-voice-dev-assistant` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-voice-dev-assistant/spec.md` (derived from `FEATURE.md`)

## Summary

Clients (Angular, Android, iOS) capture audio and render answers. A Python/FastAPI backend in
hexagonal architecture does STT, intent classification, retrieval and answer generation through
ports; Celery + Redis run ingestion and retraining; Qdrant stores vectors; Postgres stores
feedback. Docker, Kubernetes and Terraform assets live in each app's `deploy/` folder.

## Technical Context

**Language/Version**: Python 3.13+ (latest stable), TypeScript 5.8+ (Angular latest stable),
Kotlin 2.x, Swift 6.x — versions pinned at scaffold time per the constitution.

**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2/Alembic, Celery, Redis,
faster-whisper, TensorFlow/Keras + TF Serving, sentence-transformers, Qdrant client, Ollama,
Keycloak; Angular standalone + Signals; Jetpack Compose, Hilt, Retrofit/OkHttp; SwiftUI, URLSession.

**Storage**: Qdrant (vectors), Postgres (feedback, history), Redis (cache/queue), MinIO (audio, models).

**Testing**: pytest + testcontainers, Vitest/Jest + Playwright, JUnit5/MockK + Espresso,
Swift Testing/XCTest + XCUITest, golden-set ML tests.

**Target Platform**: Kubernetes (Linux containers); web, Android, iOS clients.

**Project Type**: Multi-app (backend + web + 2 mobile) with shared OpenAPI contract.

**Performance Goals**: see SC-001 to SC-004. **Constraints**: local/private processing, no
audio sent to third parties. **Scale/Scope**: 4 apps, ~5 backend capabilities, 7 stories.

## Constitution Check

| Principle | Status | How satisfied |
| :--- | :--- | :--- |
| I. Test-First | PASS | Tests precede implementation in every story; fakes + contract tests |
| II. Hexagonal | PASS | `domain/`, `application/ports`, `adapters/` with import-linter enforcement |
| III. SOLID | PASS | Small ports (`VectorWriter`/`VectorSearcher`), composition root DI |
| IV. Patterns | PASS | Strategy, Factory, Decorator, Circuit Breaker, Repository, Facade, Observer |
| V. Typed code | PASS | mypy strict, ruff, TS strict, detekt, SwiftLint |
| VI. Secure/observable | PASS | OIDC, structured logs, OTel, health endpoints |
| VII. As code | PASS | Terraform + K8s manifests + CI per app |

**Deviation (justified)**: FEATURE.md names microservices; the plan starts as one FastAPI
deployable with hexagonal modules per capability (stt, intent, retrieval, answer, ingestion)
plus Celery workers, splitting later via ports. Reduces ops cost for the MVP.

## Project Structure

### Documentation

```text
specs/001-voice-dev-assistant/
├── spec.md
├── plan.md
├── design-notes.md         # derived from UX/UI /*.html
└── tasks.md

UX/UI /                     # design references: angular.html, android.html, ios.html
```

### Source Code (per-app folders at repo root)

```text
FastApi/
├── app/
│   ├── domain/                  # entities, value objects (no framework imports)
│   ├── application/{use_cases,ports}/
│   ├── adapters/{inbound,outbound}/
│   ├── workers/                 # Celery tasks
│   └── main.py                  # composition root
├── ml/{data,glossary,prompts,training/{intent,embedder,reranker,common},evaluation,pipelines,registry,tests}/   # see TRAINING.md
├── api-contracts/openapi.yaml
├── tests/{unit,contract,integration}/
├── pyproject.toml
└── deploy/{docker,k8s,terraform}/

Angular/
├── src/app/{voice-capture,conversation,history,saved,settings,feedback,shared,core/{shell,theme,shortcuts,api}}/
├── src/styles/tokens.scss
├── e2e/
└── deploy/{docker,k8s,terraform}/

Android/
├── app/src/{main,test,androidTest}/kotlin/.../{ui,domain,data}/
└── deploy/{docker,k8s,terraform}/

IOS/
├── VoiceAssistant/{UI,Domain,Data}/
├── VoiceAssistantTests/, VoiceAssistantUITests/
└── deploy/{docker,k8s,terraform}/
```

**Structure Decision**: per-app folders as given in FEATURE.md. `deploy/` under Android and iOS
holds CI/build-environment images (Fastlane runners), mock-API stack and the Terraform for
their pipelines/distribution; the backend `deploy/` holds the runtime workloads.
The shared OpenAPI contract lives in `FastApi/api-contracts/` and generates all clients.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| Four deployable apps | Required by feature (web + 2 mobile + backend) | Cross-platform framework conflicts with native stack in FEATURE.md |
