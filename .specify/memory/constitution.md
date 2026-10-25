<!--
Sync Impact Report
- Version change: (unfilled template) → 1.0.0
- Modified principles: none renamed (template placeholders replaced by 7 concrete principles)
- Added sections: Core Principles I–VII; Technology Baseline & Version Policy;
  Security, Quality & Delivery Standards; Development Workflow & Quality Gates; Governance
- Removed sections: none
- Deferred / follow-up TODOs:
  - TODO(VERSION_BASELINE_VERIFY): The version floors in "Technology Baseline" were set from
    the author's knowledge and MUST be verified against official release pages before the
    first feature is planned; update via a PATCH/MINOR amendment if they have moved.
-->
# Multi-Platform Engineering Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)
TDD is mandatory for all production code. The Red-Green-Refactor cycle MUST be followed:
1. Write a test derived from an acceptance criterion in the spec; it MUST fail for the right reason.
2. Write the minimum code to make it pass.
3. Refactor with the suite green.

- Test pyramid: many unit tests (domain and application layers, no I/O), fewer integration
  tests (adapters against real dependencies via containers), few end-to-end/UI tests.
- Coverage MUST be ≥ 80% line and branch on domain and application code; adapter code MUST be
  covered by integration or contract tests. Coverage never substitutes for meaningful assertions.
- Tests MUST be deterministic, isolated and runnable offline; flaky tests are defects and MUST
  be fixed or quarantined with a tracked issue within one sprint.
- Tooling: Python `pytest` (+ `pytest-asyncio`, `httpx`, `hypothesis`, `testcontainers`);
  Angular Jest or Vitest + Playwright; Android JUnit5/MockK + Compose UI tests + Espresso;
  iOS Swift Testing / XCTest + XCUITest; infrastructure `terraform test`, `tflint`, `checkov`.

Rationale: tests written first force testable design and make refactoring safe.

### II. Hexagonal Architecture (Ports & Adapters)
Every service and app MUST separate three zones with dependencies pointing strictly inward:
`adapters (driving/driven) → application (use cases, ports) → domain (entities, value objects)`.

- The domain MUST NOT import frameworks, ORMs, HTTP clients, SDKs or UI toolkits.
- Ports are interfaces owned by the application/domain layer (Python `Protocol`/ABC, Kotlin
  `interface`, Swift `protocol`, TypeScript `abstract class`/`InjectionToken`).
- Adapters (FastAPI routers, SQLAlchemy repositories, Angular HTTP services, Retrofit/Room,
  URLSession/SwiftData, cloud SDKs) implement or call ports and contain no business rules.
- Wiring happens only in a composition root (FastAPI dependency providers/lifespan, Angular
  providers, Hilt/Koin modules, Swift initializer injection).
- Cross-boundary data uses explicit DTOs/mappers; domain entities MUST NOT leak into API or UI.
- Architecture rules MUST be enforced automatically (`import-linter`/`tach`, ESLint boundaries
  or Nx module boundaries, Konsist/ArchUnit-style tests, SwiftPM module separation).

Rationale: isolates business logic so it can be tested without infrastructure and so
frameworks can change without rewrites.

### III. SOLID Design
- **SRP**: one reason to change per module/class/function; handlers orchestrate, never decide.
- **OCP**: extend via new implementations (strategies, adapters), not by editing stable code.
- **LSP**: implementations MUST honor the port's contract, including errors and pre/postconditions.
- **ISP**: prefer small, role-specific ports over wide "manager" interfaces.
- **DIP**: depend on abstractions; concrete dependencies are injected, never instantiated inline.

Violations MUST be called out in review and either fixed or justified in the plan's
Complexity Tracking section.

### IV. Design Patterns, Applied Deliberately
Patterns MUST solve a demonstrated problem, be named in code/docs, and stay minimal (YAGNI).
Preferred set: Repository, Unit of Work, Factory, Strategy, Adapter, Facade, Decorator,
Observer/Domain Events, Command/CQRS (where read/write models diverge), Specification, and
Dependency Injection. Singletons via global state, service locators and speculative
abstractions are prohibited. Prefer composition over inheritance and immutability by default
(`frozen` dataclasses/Pydantic models, Kotlin `val`/data classes, Swift `struct`/`let`,
Angular signals and `readonly`).

### V. Clean, Typed, Idiomatic Code
- Python: full type hints, `mypy --strict` or `pyright` strict, `ruff` (lint + format),
  async I/O for network and database calls, no mutable default arguments.
- TypeScript/Angular: `strict` mode, standalone components, signals, new control flow
  (`@if/@for`), `OnPush` change detection, zoneless where supported, typed forms, no `any`.
- Kotlin/Android: Kotlin-first, Jetpack Compose with unidirectional data flow (ViewModel +
  `StateFlow`), coroutines/Flow with structured concurrency, `detekt` + `ktlint`.
- Swift/iOS: Swift 6 language mode with strict concurrency, SwiftUI first, `async/await` and
  actors, `SwiftLint` + `swift-format`, no force unwraps in production code.
- Functions SHOULD stay under ~30 lines and cyclomatic complexity ≤ 10; names MUST express intent.
- Public APIs and non-obvious decisions MUST be documented; comments explain why, not what.

### VI. Secure, Observable, Reliable by Default
- Secrets MUST NOT be committed or hardcoded; use a secret manager or environment injection.
- All external input MUST be validated at the boundary (Pydantic models, Angular typed forms,
  server-side re-validation); output MUST be encoded; errors MUST NOT leak stack traces/SQL.
- AuthN/Z uses OAuth 2.1/OIDC with least privilege; mobile apps store tokens in Keystore /
  Keychain, enforce TLS, and never log PII or credentials.
- Services MUST emit structured JSON logs with correlation IDs, OpenTelemetry traces and
  metrics, and expose `/health/live` and `/health/ready` endpoints.
- Remote calls MUST define timeouts, retries with backoff and idempotency where applicable.
- Dependencies MUST be pinned, scanned (SCA/SAST/secret scanning) and updated continuously.

### VII. Everything as Code, Immutable and Reproducible
Infrastructure, pipelines, environments and policies MUST be declared in version control and
applied via CI/CD; manual changes to shared environments are prohibited. Builds MUST be
reproducible (lockfiles, pinned base images by digest), artifacts immutable and promoted, not
rebuilt, between environments. API contracts (OpenAPI) are the source of truth between
clients and services and MUST be versioned; breaking changes require a new major version.

## Technology Baseline & Version Policy

New work MUST target the **latest stable release** of each technology below, verified against
the official release page at spec time. The floors in this table are minimums; falling below a
floor requires a documented exception. Versions MUST be pinned in lockfiles/manifests and
reviewed at least quarterly; versions that reach end-of-life MUST be upgraded before EOL.
No alpha/beta/RC releases in production.

| Area | Baseline (floor) | Notes |
| :--- | :--- | :--- |
| Python | 3.13+ (prefer latest stable, e.g. 3.14) | `uv` for envs/locking, `pyproject.toml`, `ruff`, `mypy`/`pyright` |
| FastAPI | latest stable 0.1xx+ with Pydantic v2, SQLAlchemy 2.x, Alembic, Uvicorn/Gunicorn | Async endpoints, `Annotated` dependencies, lifespan handlers, no deprecated `on_event` |
| Angular | latest stable major (20+) with TypeScript 5.8+, Node.js active LTS | Standalone APIs, signals, Vitest/Jest, Angular CLI builders (esbuild/Vite) |
| Android | Kotlin 2.x, AGP latest stable, `compileSdk`/`targetSdk` = latest stable API (36+), `minSdk` ≥ 26 | Compose, Hilt, Room, version catalogs (`libs.versions.toml`), 16 KB page-size support |
| iOS | Swift 6.x, latest stable Xcode, iOS deployment target ≤ N-1 of latest major | SwiftUI, Swift Package Manager, Swift Testing, privacy manifests |
| Docker | Docker Engine/BuildKit latest stable, Compose v2 | See container rules below |
| Kubernetes | A currently supported minor (latest stable minus at most 1) | Helm 3 or Kustomize; GitOps (Argo CD/Flux) preferred |
| Terraform | Latest stable 1.x (OpenTofu-compatible modules where feasible) | Remote state with locking, pinned provider versions |

**Container rules**: multi-stage builds; minimal/distroless or slim base images pinned by
digest; run as non-root with read-only root filesystem; no secrets in layers; `.dockerignore`
required; `HEALTHCHECK` defined; images scanned (Trivy/Grype) and signed (cosign) with SBOMs.

**Kubernetes rules**: declarative manifests only; resource requests/limits, liveness/readiness/
startup probes, `PodDisruptionBudget` and HPA for production workloads; `securityContext`
(non-root, drop all capabilities, `seccompProfile: RuntimeDefault`); NetworkPolicies default
deny; Pod Security Standards "restricted"; secrets via External Secrets/CSI, never plain
manifests; one namespace per environment/team with RBAC least privilege.

**Terraform rules**: small versioned modules with typed, validated variables and documented
outputs; remote backend with state locking and encryption; no secrets in state or variables
files; `terraform fmt`, `validate`, `tflint`, `checkov`/`trivy config` and a reviewed `plan`
MUST pass before `apply`; `apply` runs only from CI with approval for production.

## Security, Quality & Delivery Standards

- **API design**: REST with OpenAPI 3.1, consistent error envelope (RFC 9457 Problem Details),
  pagination, idempotency keys for unsafe retries, and explicit versioning.
- **Performance**: define and test budgets per spec (e.g. API p95 latency, Angular Core Web
  Vitals, Android cold-start, iOS launch time); regressions block release.
- **Accessibility & UX**: WCAG 2.2 AA for web; TalkBack/VoiceOver support and dynamic type on mobile.
- **Data**: migrations are versioned, forward-compatible and reversible; PII is classified,
  minimized and encrypted in transit and at rest.
- **Static quality gates**: lint, format, type-check, SAST, SCA and secret scan MUST pass in CI;
  no new critical/high findings may be merged.
- **Mobile release**: signed builds, staged rollouts, crash reporting, and no debug code or
  logging in release builds.

## Development Workflow & Quality Gates

1. **Spec first**: work starts from an approved spec (`/speckit-specify` → `/speckit-plan` →
   `/speckit-tasks`); no implementation without it.
2. **Constitution check**: every plan MUST pass a gate against these principles; deviations are
   recorded with justification in Complexity Tracking.
3. **Branching**: trunk-based or short-lived feature branches; Conventional Commits;
   small, reviewable PRs.
4. **Pull requests**: require ≥ 1 peer review (≥ 2 for security-sensitive or infrastructure
   changes), green CI, tests added first (visible in history), and updated docs/ADRs.
5. **CI/CD pipeline stages**: lint/type-check → unit tests → integration tests (containers) →
   build image/app → security scans → deploy to ephemeral/staging → smoke/E2E → gated
   promotion to production with rollback plan.
6. **Architecture Decision Records** MUST be written for significant technology or pattern
   choices and stored in `docs/adr/`.
7. **Definition of Done**: acceptance criteria met, tests green and ≥ coverage target, gates
   passed, observability in place, documentation updated, and no unresolved review comments.

## Governance

This constitution supersedes all other practices and conventions in this repository. In any
conflict, the constitution wins; project-level guides MUST NOT contradict it.

- **Amendments**: proposed via PR that includes the rationale, a Sync Impact Report, and a
  migration plan for affected specs/plans/code. Approval requires at least two maintainers.
- **Versioning**: semantic versioning. MAJOR = backward-incompatible principle removal or
  redefinition; MINOR = new principle/section or materially expanded guidance (including raising
  version floors); PATCH = clarifications and wording fixes.
- **Compliance review**: every PR and plan MUST verify compliance; reviewers MAY block merges
  on violations. The constitution is reviewed at least quarterly, including the technology
  version baseline.
- **Exceptions**: time-boxed, documented with owner and expiry in the plan's Complexity
  Tracking section, and tracked to closure.

**Version**: 1.0.0 | **Ratified**: 2026-10-24 | **Last Amended**: 2026-10-24
