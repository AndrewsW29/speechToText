# Voice-Driven Developer Assistant: Detailed Architecture
# Frameworks to use to build the software
- Python Fast Api, Redis, Celery, Vector Database, Angular for Web, Android Kotlin, IOS Swift, Docker, Kubernetes, Terraform
# Software layout structure folder layout
1. Folder FastApi main root path for backend
1. a. Docker files: deploy/docker
1. b. Kubernetes files: deploy/k8s
1. c. Terraform files: deploy/terraform

2. Folder IOS main root path for ios mobile application
2. a. Docker files: deploy/docker
2. b. Kubernetes files: deploy/k8s
2. c. Terraform files: deploy/terraform

3. Folder Android main root path for android mobile application
3. a. Docker files: deploy/docker
3. b. Kubernetes files: deploy/k8s
3. c. Terraform files: deploy/terraform

4. Folder Angular main root path for Angular WEB application
4. a. Docker files: deploy/docker
4. b. Kubernetes files: deploy/k8s
4. c. Terraform files: deploy/terraform

5. UX/UI Folder DESIGNS 



Where an exact current version is uncertain, this document says "latest stable". Pin versions when you scaffold.

## 1. Big picture

- **Goal:** a user speaks ("how do I create a controller and a service in Java?"), the speech becomes text, the backend understands the intent, retrieves relevant knowledge from a vector DB, and returns an answer or task result.
- **Clients:** Angular (web), Kotlin (Android), Swift (iOS). They capture audio and render results. They contain no business logic.
- **Backend:** Python services in hexagonal architecture, packaged as containers and deployed on Kubernetes.
- **Learning:** a feedback loop (thumbs up/down, "was this useful?") feeds retraining of TensorFlow models.

**Early decision: where does speech-to-text run?**

| Option | Pros | Cons |
|---|---|---|
| **A. Server-side** (clients upload audio, backend runs faster-whisper) | One consistent model, works the same on all 3 clients, fully local/private | Needs audio upload, server compute |
| **B. On-device** (Android `SpeechRecognizer`, iOS `Speech` framework, whisper.cpp) | Low latency, works offline | Different engines per platform, uneven accuracy. Web Speech API in Chrome sends audio to Google, so it is not local |

**Recommendation:** A as the default, with STT behind a port so B can be added later without touching the core.

## 2. End-to-end flow

1. The client records audio (WebM/Opus on web, M4A/AAC on iOS, Ogg/Opus or AAC on Android).
2. It sends the audio to the API Gateway over HTTPS (upload, or WebSocket for streaming).
3. The **STT Service** converts it to text with timestamps.
4. The **Intent Service** (TensorFlow) classifies the request, for example `CREATE_CODE_ARTIFACT`, `EXPLAIN_CONCEPT`, or `FIND_DOCS`, and extracts entities such as `language=Java`, `artifact=[controller, service]`.
5. The **Retrieval Service** embeds the query, searches the vector DB (filtered by `language=java`), and reranks.
6. The **Answer Service** composes the response, either from templates and snippets or through a local LLM (Ollama) given the retrieved context.
7. The client displays the result and offers feedback buttons.
8. Feedback is stored, and a scheduled job retrains the models.

## 3. Backend: Hexagonal Architecture (Ports & Adapters)

**Principle:** the domain core knows nothing about frameworks, databases, or models. Everything external plugs in through interfaces (ports) with swappable implementations (adapters).

```
        Driving adapters (inbound)              Driven adapters (outbound)
   ┌──────────────────────────────┐      ┌────────────────────────────────┐
   │ REST (FastAPI)  WebSocket    │      │ FasterWhisperTranscriber       │
   │ gRPC  CLI                    │      │ TFIntentClassifier             │
   └──────────────┬───────────────┘      │ QdrantVectorStore              │
                  │                      │ SentenceTransformerEmbedder    │
          ┌───────▼────────┐             │ OllamaLLM                      │
          │ Inbound ports  │             │ PostgresFeedbackRepo           │
          │ (use cases)    │             └───────────────▲────────────────┘
          └───────┬────────┘                             │
          ┌───────▼──────────────────────────────────────┴──┐
          │  Application layer: use cases / orchestration    │
          │  ┌───────────────────────────────────────────┐  │
          │  │ Domain: entities, value objects, rules    │  │
          │  └───────────────────────────────────────────┘  │
          │  Outbound ports (interfaces) defined here        │
          └──────────────────────────────────────────────────┘
```

### Layers

- **Domain** (pure Python, no imports from frameworks)
  - Entities: `Query`, `Intent`, `KnowledgeChunk`, `Answer`, `Feedback`
  - Value objects: `Transcript`, `Language`, `Embedding`, `Confidence`
  - Example rule: `Answer` cannot be created with an empty source list.
- **Application** (use cases and ports)
  - Inbound ports: `AskQuestionUseCase`, `IngestDocumentUseCase`, `SubmitFeedbackUseCase`
  - Outbound ports: `Transcriber`, `IntentClassifier`, `Embedder`, `VectorStore`, `AnswerGenerator`, `FeedbackRepository`
- **Adapters** (infrastructure)
  - Inbound: FastAPI routers, WebSocket handlers
  - Outbound: faster-whisper, TensorFlow/Keras, Qdrant, Ollama, Postgres

### Example: a port and its adapter

```python
# application/ports/transcriber.py
from abc import ABC, abstractmethod
from domain.transcript import Transcript

class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio: bytes, language: str | None = None) -> Transcript: ...
```

```python
# adapters/outbound/stt/faster_whisper_transcriber.py
import io
from faster_whisper import WhisperModel
from application.ports.transcriber import Transcriber
from domain.transcript import Transcript

class FasterWhisperTranscriber(Transcriber):
    def __init__(self, model_size: str = "small"):
        self._model = WhisperModel(model_size, compute_type="int8")

    def transcribe(self, audio: bytes, language=None) -> Transcript:
        segments, info = self._model.transcribe(io.BytesIO(audio), language=language)
        return Transcript(text=" ".join(s.text for s in segments), language=info.language)
```

### Example: a use case that depends only on ports

```python
# application/use_cases/ask_question.py
class AskQuestion:
    def __init__(self, transcriber: Transcriber, classifier: IntentClassifier,
                 embedder: Embedder, store: VectorStore, generator: AnswerGenerator):
        self._t, self._c, self._e, self._s, self._g = transcriber, classifier, embedder, store, generator

    def execute(self, audio: bytes) -> Answer:
        transcript = self._t.transcribe(audio)
        intent = self._c.classify(transcript.text)            # e.g. CREATE_CODE_ARTIFACT
        vector = self._e.embed(transcript.text)
        chunks = self._s.search(vector, filters=intent.entities, top_k=5)
        return self._g.generate(transcript.text, intent, chunks)
```

Because the use case sees only interfaces, you can test it with fakes and swap Qdrant for Chroma without changing it.

## 4. SOLID, applied concretely

- **S: Single Responsibility.** `FasterWhisperTranscriber` only transcribes. Chunking, embedding, and storing are separate classes.
- **O: Open/Closed.** Add a new STT engine (`VoskTranscriber`) by adding a class, with no edits to `AskQuestion`.
- **L: Liskov Substitution.** Any `VectorStore` implementation (Qdrant, in-memory fake) must honor the same contract: `search` returns results sorted by score, descending. Contract tests run against every implementation.
- **I: Interface Segregation.** Split `VectorStore` into `VectorWriter` and `VectorSearcher`. The ingestion pipeline needs only the writer, and the query path needs only the searcher.
- **D: Dependency Inversion.** The use case depends on the `Transcriber` abstraction. A composition root (`main.py`) wires the concrete classes.

## 5. Design patterns and where they fit

| Pattern | Where | Example |
|---|---|---|
| **Strategy** | Interchangeable algorithms | Chunking strategies (by sentence, by tokens, by timestamp), ranking strategies |
| **Factory / Abstract Factory** | Creating adapters from config | `TranscriberFactory.create("whisper" \| "vosk")` |
| **Adapter** | Wrapping third-party libs | Qdrant client behind `VectorStore` |
| **Chain of Responsibility** | Request pipeline | Preprocess → VAD → STT → normalize → intent |
| **Decorator** | Cross-cutting concerns | `CachedEmbedder(Embedder)`, `LoggingVectorStore(VectorStore)` |
| **Observer / Event bus** | Decoupled reactions | `AnswerDelivered` event triggers analytics. `FeedbackSubmitted` event queues retraining |
| **Repository** | Persistence abstraction | `FeedbackRepository`, `DocumentRepository` |
| **Facade** | Simple API over a complex subsystem | `IngestionFacade.ingest(repo_url)` |
| **Builder** | Complex objects | `AnswerBuilder` assembling text, sources, confidence, and snippets |
| **Circuit Breaker** | Resilience | Wrap the Ollama call so a slow LLM degrades gracefully to retrieval-only answers |
| **CQRS** (architectural) | Separate read/write paths | Ingestion (write) and query (read) scale independently |

On the client side, use **MVVM** (Android and iOS) and **Smart/Dumb components** with signals (Angular).

## 6. TDD workflow

- **Red → Green → Refactor** on every use case. Write the failing test first, with fakes for the ports.
- **Test pyramid**
  - **Unit** (the majority): domain and use cases with in-memory fakes. Tools: `pytest`, Kotlin `JUnit5 + MockK`, Swift `XCTest`, Angular `Jest` or `Vitest`.
  - **Contract tests:** one shared suite that every adapter of a port must pass (`VectorStore`, `Transcriber`).
  - **Integration:** real Qdrant and Postgres through `testcontainers`.
  - **E2E:** Playwright (web), Espresso (Android), XCUITest (iOS), plus a short suite against a staging cluster.
- **ML-specific tests**
  - Golden-set tests: 200 labeled utterances must reach at least X% intent accuracy, and CI fails if a new model drops below the threshold.
  - Retrieval tests: for known questions, the expected chunk must appear in the top-k (recall@k).
  - STT tests: a few recorded audio samples with a word-error-rate threshold.

Example first test, written before any implementation:

```python
def test_ask_question_returns_sources_for_java_controller_request():
    uc = AskQuestion(
        transcriber=FakeTranscriber("how do I create a controller in Java"),
        classifier=FakeClassifier(Intent("CREATE_CODE_ARTIFACT", {"language": "java"})),
        embedder=FakeEmbedder(), store=InMemoryVectorStore(seed=JAVA_DOCS),
        generator=EchoGenerator())
    answer = uc.execute(b"audio-bytes")
    assert answer.sources and "controller" in answer.text.lower()
```

## 7. The "model that learns": what TensorFlow actually does

TensorFlow is not a chatbot by itself. Split the intelligence into parts:

- **Intent and entity classifier (TensorFlow/Keras).** A small Transformer or BiLSTM trained on labeled utterances. Example: "make a Spring service" maps to `CREATE_CODE_ARTIFACT` with `{framework: spring, artifact: service}`. Export as SavedModel and serve with **TF Serving**, or use TFLite on mobile.
- **Embedding model.** Start with a pretrained one and later **fine-tune it in TensorFlow** with a two-tower setup on (query, helpful chunk) pairs from user feedback. This is how retrieval gets better as people use it.
- **Reranker (TensorFlow).** A cross-encoder or learning-to-rank model that reorders the top 20 retrieved chunks using click and feedback data.
- **Answer generation.** Retrieval-Augmented Generation (RAG) with a local LLM through Ollama. TensorFlow is not a good fit for the LLM itself.

**Learning loop**

1. Store every interaction: transcript, intent, retrieved chunk IDs, answer, and the user's feedback.
2. A scheduled job (Kubernetes `CronJob`) builds a training set from positive and negative feedback.
3. It retrains or fine-tunes the intent, embedding, and reranker models and evaluates them on the golden set.
4. If metrics improve, it registers the new model version (**MLflow** or TF Model Registry) and rolls it out with a canary deployment.
5. Keep a human review step for low-confidence samples so bad feedback does not poison the model.

**Cold start:** you need training data first. Write 50-100 example utterances per intent and use an LLM to expand them. Then let real usage take over.

## 8. Vector database design

- **Choice:** **Qdrant**. It is open source, has strong metadata filtering, and has an official Helm chart for Kubernetes.
- **Collections**
  - `code_knowledge`: chunks of docs, tutorials, and snippets
  - `user_history` (optional): per-user memory
- **Payload per chunk:** `{id, text, language: "java", framework: "spring", artifact_type: "controller", source_url, version, created_at}`
- **Ingestion pipeline:** source (docs, repos, wikis) → parse → chunk (code-aware, split by class or method) → embed → upsert with an idempotent ID (hash of content).
- **Search:** hybrid search (dense vectors plus keyword/BM25) with filters such as `language == "java"` on top. This matters for code, where exact names like `@RestController` should match exactly.
- **Example:** the query "create a controller and service in Java" filters to `language=java` and `framework=spring`, retrieves the `@RestController` and `@Service` chunks, and the reranker puts the most complete tutorial first.

## 9. Clients

**Angular (latest stable, standalone components + Signals)**

- Record with `MediaRecorder`, and send audio to the API.
- Structure by feature: `voice-capture`, `conversation`, `history`, `feedback`.
- State with Signals or NgRx SignalStore. Use a typed API client generated from the OpenAPI spec.
- Tests: Jest/Vitest for units, Playwright for E2E.

**Android (Kotlin, Jetpack Compose)**

- `MediaRecorder` or `AudioRecord` for capture. Retrofit/OkHttp for the API, and OkHttp WebSocket for streaming.
- Clean architecture + MVVM: `ui` → `ViewModel` → `UseCase` → `Repository` (interface) → `RemoteDataSource`.
- Hilt for dependency injection, Coroutines/Flow for async.
- Optional TFLite for on-device intent classification (offline fallback).

**iOS (Swift, SwiftUI)**

- `AVAudioRecorder`/`AVAudioEngine` for capture. `URLSession` async/await for networking.
- MVVM, with protocols for repositories (the Swift equivalent of ports). Swift Concurrency for async.
- Optional Core ML or TFLite for on-device classification.

**Shared across all three**

- An OpenAPI contract is the single source of truth. Generate the TypeScript, Kotlin, and Swift clients from it.
- Authentication with OAuth2/OIDC (Keycloak, which is open source and self-hostable) and JWT.

## 10. Deployment: Docker and Kubernetes

**Services (one container each)**

- `api-gateway`: auth, routing, rate limiting (Kong, or Nginx Ingress plus a FastAPI BFF)
- `stt-service`: faster-whisper (GPU node pool if available)
- `intent-service`: TF Serving
- `retrieval-service` and `answer-service`
- `ingestion-worker`: processes queued ingestion jobs
- Data stores: Qdrant (StatefulSet), Postgres, Redis (cache and queue), MinIO (audio/object storage)
- Training: `CronJob` or Argo Workflows, with MLflow for the model registry

**Docker practices**

- Multi-stage builds, slim or distroless base images, non-root user, pinned versions, `.dockerignore`.
- Scan images with Trivy in CI.

**Kubernetes**

- Package with **Helm** or Kustomize, with separate overlays for `dev`, `staging`, and `prod`.
- `Deployment` plus `HorizontalPodAutoscaler` for stateless services. Scale `stt-service` on queue length or CPU.
- `StatefulSet` plus `PersistentVolumeClaim` for Qdrant and Postgres.
- Liveness and readiness probes, resource requests/limits, and `NetworkPolicy` to restrict traffic between pods.
- Secrets through Sealed Secrets or External Secrets. Ingress with TLS (cert-manager).
- Observability: Prometheus, Grafana, Loki, and OpenTelemetry tracing across the audio → answer path.
- **CI/CD:** GitHub Actions or GitLab CI runs lint → tests → build images → scan → push → Argo CD (GitOps) deploys. Mobile builds go through Fastlane.
- Practical tip: develop locally with Docker Compose, or `kind`/`minikube`, before touching a real cluster.

## 11. Repository layout (monorepo)

```
voice-assistant/
├── backend/
│   ├── gateway/
│   ├── stt_service/        # each service follows the same hexagonal layout:
│   │   ├── domain/
│   │   ├── application/    #   use_cases/, ports/
│   │   ├── adapters/       #   inbound/, outbound/
│   │   ├── main.py         #   composition root (wiring)
│   │   └── tests/          #   unit/, contract/, integration/
│   ├── intent_service/
│   ├── retrieval_service/
│   └── ingestion_worker/
├── ml/
│   ├── training/           # TF pipelines, datasets, evaluation
│   ├── golden_sets/
│   └── notebooks/
├── clients/
│   ├── web-angular/
│   ├── android-kotlin/
│   └── ios-swift/
├── api-contracts/          # openapi.yaml
├── deploy/
│   ├── docker/
│   └── helm/
└── docs/                   # ADRs, diagrams
```

## 12. Suggested roadmap

1. **Walking skeleton:** one use case end to end (record audio → text → fixed answer) across web, backend, and Docker Compose. Tests first.
2. **Retrieval:** ingest Java and Spring documentation into Qdrant and answer from the top chunks.
3. **Intent model:** train a first TensorFlow classifier on a hand-built dataset and add the golden-set test to CI.
4. **RAG answers:** add the local LLM with a circuit breaker.
5. **Mobile clients:** Android and iOS against the same OpenAPI contract.
6. **Feedback loop and retraining:** feedback storage, `CronJob`, model registry, canary rollout.
7. **Kubernetes hardening:** autoscaling, observability, security policies.

## 13. Open decisions

- Is the knowledge source your own documentation and code repos, public docs (Spring, Java), or both? This sets the ingestion work.
- Should answers be generated text (needs a local LLM and decent hardware) or retrieved snippets only?
- Is the backend fixed on Python? It is assumed so because of TensorFlow and faster-whisper. A Kotlin/Spring gateway in front of the Python ML services is also a reasonable split.
