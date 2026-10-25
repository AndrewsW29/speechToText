# Vector Database Structure for the Voice Developer Assistant Platform

Companion to [FEATURE.md](FEATURE.md), [DESIGN.md](DESIGN.md), [TRAINING.md](TRAINING.md) and [PDF_LEARNING.md](PDF_LEARNING.md). The template-first response feature (TEMPLATE_RESPONSES.md) is being written in a separate session and uses the `templates` collection defined here.

This document defines the vector database layout for the whole platform: what is stored, in which collection, with which vectors, payload fields, indexes, and filters, and how the same database supports retrieval, template routing, caching, memory, and the training and learning loops. Engine: **Qdrant** (open source, runs locally on Kubernetes).

**What was verified.** REST bodies and settings were checked against the official Qdrant documentation on 2026-10-25 (the docs describe the 1.19 line). Version-sensitive items are flagged in section 6. Five behaviours could not be confirmed from the docs and are marked **verify**: each has a contract test in section 13. The search parameters `hnsw_ef`, `exact`, `score_threshold`, the `with_payload` include list, and `wait=true` follow the Qdrant API reference as I know it and were not re-fetched, so the real-server tests in section 13 exercise them too. The Python helpers in section 12 were run and their tests pass. No Qdrant server was started, so no request was executed against a real server.

## Contents

1. Principles
2. Where the vector database sits
3. Collection catalog
4. Naming, versioning, and collection resolution
5. Collection specifications
6. Creating collections and indexes
7. Query catalog
8. How the vector database serves training and learning
9. Multi-tenancy, access control, and security
10. Performance, memory, and sizing
11. Operations on Kubernetes
12. Ports, adapters, and code
13. Testing (TDD)
14. Migration playbook
15. Risks and mitigations
16. Roadmap
17. Open questions

---

## 1. Principles

- **The vector database is a derived index, not the system of record.** Postgres holds canonical chunk text, metadata, feedback, and registries. MinIO holds files. Any collection can be rebuilt by re-embedding from Postgres. Example: a corrupted collection is replaced by re-running the reindex job, with no data loss.
- **One collection per purpose and embedder version.** Vectors from different embedding models are never comparable, so they never share a collection. Example: `code_knowledge__emb_v3__s1` and `code_knowledge__emb_v4__s1` exist side by side during a migration.
- **One shared collection for all tenants, partitioned by payload.** This is Qdrant's recommended multitenancy approach: a separate collection per tenant is rarely efficient. `tenant_id` gets a tenant index, and access control is enforced in the adapter. Dedicated collections are for the few tenants that need strict isolation.
- **Index only the fields you filter on, and create the payload indexes before loading data.** Qdrant's filterable HNSW adds graph edges only after a payload index exists, so indexes created after ingestion do not give the full benefit.
- **Deterministic point ids.** The point id is a UUIDv5 of the canonical id (`c_5f3a`, `u-00123`), so re-running ingestion updates points instead of duplicating them (PDF_LEARNING F47).
- **An upsert replaces the whole point's vectors.** Re-uploading an existing id deletes and reinserts the point with only the vectors you send, so omitted named vectors become empty. Use payload operations for payload-only changes.
- **Keep payload lean.** Child chunk text is stored because retrieval needs it immediately. Parent sections live in Postgres and are fetched by `parent_id`. Images and audio live in MinIO.
- **Everything is versioned.** Every point carries `schema_version`, `embedder_version`, and (for chunks) `pipeline_version`. Collections carry the same in their metadata.
- **Design for deletion and lineage.** Fields like `doc_id`, `source_doc_id`, and `depends_on_doc_ids` make "delete everything derived from this PDF" a single filter.
- **Fail closed.** A query without a tenant and ACL subjects is an error, never "search everything".

## 2. Where the vector database sits

```
 ingestion (Celery) ──▶ Postgres: canonical chunks, metadata, feedback, registries
        │                          │  rebuild / reindex
        ▼                          ▼
 embedder (TF Serving) ──────▶ Qdrant: vectors + filterable payload (derived)
        ▲                                  │
 query path (FastAPI):                     │
 STT ▶ intent ▶ scope filter ──────────────┘▶ top-k ▶ rerank (TF) ▶ answer
 training jobs (Kubernetes Job): feedback (Postgres) + hard negatives (Qdrant)
        ▶ datasets (DVC) ▶ new embedder ▶ new collections ▶ evaluate ▶ promote
```

| Data | System of record | What Qdrant holds | Why |
|---|---|---|---|
| Documents and versions, original files | Postgres (metadata), MinIO (files) | `doc_id` references only | Not searched by similarity |
| Chunk text and metadata | Postgres `chunks` | Copy of child chunk text and filter fields | Any collection can be rebuilt by re-embedding |
| Parent sections (small-to-big) | Postgres `parent_sections` | `parent_id` only | Large text, fetched by id after the search |
| Feedback, traces, review queue | Postgres | Nothing (aggregates are synced into `quality_score`) | Frequent writes and relational queries |
| Glossary, template registry | Postgres and Git (templates) | Searchable copies | Reviewed, versioned artifacts |
| Cached answer bodies | Redis | Cached question vectors and an `answer_ref` | Bodies are large and short-lived |
| Training datasets | DVC (object storage) | Embeddings of utterances for hygiene checks | Datasets are versioned files |
| Index registry (names, states, metrics, alias map) | Postgres `index_registry` | Copy in collection metadata | Collection snapshots do not include aliases |

## 3. Collection catalog

| Alias | Physical name (example) | One point is | Vectors | Tenancy | Retention | Phase |
|---|---|---|---|---|---|---|
| `code_knowledge` | `code_knowledge__emb_v3__s1` | One chunk: prose, code, table, table row, figure caption, or summary | `dense` + `sparse` | Shared, `tenant_id` + `acl` | Until the document is deleted or superseded | MVP |
| `templates` | `templates__emb_v3__s1` | One example utterance or description of a template | `dense` | Global, with tenant overrides | Until the template is deprecated | v1 |
| `semantic_cache` | `semantic_cache__emb_v3__s1` | One cached question | `dense` | Shared, scoped by `scope_hash` | Hours to days (`expires_at`) | v1 |
| `utterances` | `utterances__emb_v3__s1` | One labeled or production utterance | `dense` | Shared, `tenant_id`, consent flags | Dataset policy, deleted on consent withdrawal | v1 |
| `glossary_terms` | `glossary_terms__emb_v3__s1` | One term with aliases and definition | `dense` | Global, tenant, or user scope | Until rejected or deleted | v1 |
| `user_memory` | `user_memory__emb_v3__s1` | One memory item (summary or fact) | `dense` | Per user (`user_hash`) | Per user policy (`expires_at`) | v2 |
| `page_regions` | `page_regions__colpali_v1__s1` | One page image | `pages` (multivector) | Shared, `tenant_id` + `acl` | With the document | v2, optional |

**Controlled vocabularies.** Free-form values drift ("spring", "Spring Boot", "springboot"). The allowed values for `framework`, `artifact_type`, `language`, `chunk_type`, and `source_type` live in a Postgres `taxonomy` table. The adapter validates them on write and rejects unknown values. Starting values:

| Field | Values |
|---|---|
| `language` (programming language) | `java`, `kotlin`, `typescript`, `swift`, `python` |
| `framework` | `spring-boot`, `spring-framework`, `angular`, `android`, `swiftui`, `fastapi` |
| `artifact_type` | `controller`, `service`, `repository`, `model`, `dto`, `config`, `test`, `component` |
| `chunk_type` | `text`, `code`, `table`, `table_row`, `figure_caption`, `summary` |
| `source_type` | `pdf`, `web_doc`, `repo`, `wiki`, `note` |

Note: earlier documents used `framework: "spring"` as shorthand. Use `spring-boot` or `spring-framework` once the taxonomy exists. In every collection, `language` means the **programming** language, and the spoken or written language is `natural_language` (`en`, `es`). PDF_LEARNING F17 should be read that way.

## 4. Naming, versioning, and collection resolution

- **Pattern:** `{purpose}__{embedder}__s{schema}`. Example: `code_knowledge__emb_v3__s1`.
  - `embedder` is the version label of the embedding model in the model registry (changes when you fine-tune or swap the model).
  - `schema` is the layout version (vector names, field meanings). Adding a payload field does not need a bump. Changing a field's meaning or adding a vector does.
- **Index registry (Postgres `index_registry`).** One row per physical collection: `collection`, `purpose`, `embedder_version`, `schema_version`, `status`, `alias`, `points_expected`, `points_loaded`, `golden_recall_at_5`, `golden_mrr`, `created_at`, `live_since`, `retired_at`, `snapshot_ref`. Status moves `building`, `verifying`, `shadow`, `live`, `retired`.
- **Collection metadata (Qdrant 1.16+).** Each collection stores `embedder_version`, `schema_version`, and `purpose` in its `metadata`, and the service checks them at startup.
- **Resolution rule.** A service does **not** hard-code an alias. It embeds the query, learns the embedder version that produced the vector, and asks the registry for the live collection built with that same version (`resolve_collection` in section 12). This removes the cutover race: while an embedder is being rolled out gradually, old pods query the old collection and new pods query the new one. A query vector can never meet a collection from another model.
- **Aliases** (`code_knowledge`) still exist for tools, dashboards, and for changes where the embedder stays the same (schema change, resharding). Qdrant applies several alias actions in one request atomically, so the alias never points nowhere. Collection snapshots do not include aliases, so the alias map is also kept in the registry.

Example registry rows during an embedder rollout:

| collection | embedder_version | status |
|---|---|---|
| `code_knowledge__emb_v3__s1` | `emb_v3` | `live` |
| `code_knowledge__emb_v4__s1` | `emb_v4` | `shadow` |

When `emb_v4` passes its gates and the canary, the registry flips both rows in one transaction (`emb_v4` to `live`, `emb_v3` to `retired`).

## 5. Collection specifications

### 5.1 `code_knowledge`: the main knowledge collection

- **Purpose:** retrieval-augmented answers from PDFs, web docs, repositories, and notes (FEATURE.md section 8, PDF_LEARNING F18 to F25).
- **Point:** one chunk. Prose, code, tables (Markdown), table rows (one sentence per row), figure captions, and summaries are separate points distinguished by `chunk_type`.
- **Vectors**
  - `dense`: size = the embedder's output dimension (768 is used in examples), distance `Cosine`, L2-normalized at ingestion, which matches the normalized training objective in TRAINING.md section 4.2.
  - `sparse`: BM25-style term weights (or a learned sparse model) for exact names such as `@Transactional`. Sparse vectors support dot product only. Points may omit `sparse` (a figure caption with no text, for example).
- **Payload**

| Field | Type | Indexed | Purpose |
|---|---|---|---|
| `chunk_id` | keyword | no | Canonical id (Postgres key). The point id is the UUIDv5 of it |
| `tenant_id` | keyword | tenant index | Isolation (section 9) |
| `acl` | keyword[] | keyword | Subjects allowed to read: `user:u_7c1d`, `team:platform`, `tenant:acme`, `public` |
| `doc_id` | keyword | keyword | "This document" scope, deletion, citations |
| `doc_version` | integer | integer | Version diff and supersede |
| `is_latest` | bool | bool | Default filter. `valid_to` keeps the history |
| `source_type` | keyword | keyword | `pdf`, `web_doc`, `repo`, `wiki`, `note` |
| `chunk_type` | keyword | keyword | `text`, `code`, `table`, `table_row`, `figure_caption`, `summary` |
| `language` | keyword | keyword | Programming language |
| `natural_language` | keyword | keyword | `en`, `es` |
| `framework` | keyword | keyword | From the taxonomy |
| `framework_version` | keyword | no | `3.5`. Reranker feature, not a hard filter |
| `artifact_type` | keyword | keyword | `controller`, `service`, ... |
| `topic_tags` | keyword[] | keyword | Tags from auto-tagging (PDF_LEARNING F35) |
| `text` | string | no | Child chunk text for the reranker and generator |
| `context_header` | string | no | Breadcrumb prepended before embedding |
| `section_path` | keyword[] | no | `["Web", "Creating a REST Controller"]` |
| `parent_id` | keyword | no | Key of the parent section in Postgres (small-to-big) |
| `page_start`, `page_end` | integer | integer (range only) | "Pages 40 to 60" scope and citations |
| `page_label` | keyword | no | Printed page number |
| `bbox` | list of `[page, x0, y0, x1, y1]` | no | Viewer highlight |
| `title`, `source_url` | string | no | Display |
| `license` | keyword | no | Compliance |
| `quality_score` | float | no | Ranking feature, synced from Postgres every few minutes |
| `ocr_confidence` | float | no | Quality flag |
| `is_generated` | bool | bool | Marks LLM-written text (captions, summaries) |
| `text_hash` | keyword | no | Change detection and dedupe |
| `created_at` | datetime | datetime | Freshness filter |
| `valid_from`, `valid_to` | datetime | no | History |
| `embedder_version`, `pipeline_version`, `schema_version` | keyword | no | Guards and reprocessing |

- **Why `is_latest` and not `valid_to is null`:** a boolean index is a cheap, explicit filter. PDF_LEARNING F24 used `valid_to` is null. Keep both fields and filter on `is_latest`.

### 5.2 `utterances`: training data hygiene and kNN

- **Purpose:** hold the embeddings of every labeled and production utterance so you can find duplicates, leakage, label noise, drift, and the most informative items to label (section 8).
- **Point:** one utterance. **Vector:** `dense` only (embedding of the normalized text).
- **Source of truth:** the dataset store (DVC) and Postgres. Splits are decided by the dataset build and mirrored here for similarity checks.

| Field | Type | Indexed | Purpose |
|---|---|---|---|
| `utt_id` | keyword | no | Canonical id (`u-00123`) |
| `text`, `raw_text` | string | no | Normalized text and the raw ASR output |
| `intent` | keyword | keyword | Label, or `UNLABELED` |
| `slots` | list of `{label, text}` | no | Entity spans |
| `slot_labels` | keyword[] | keyword | "All utterances that mention a FIELD" |
| `source` | keyword | keyword | `seed`, `template`, `llm`, `asr_augmented`, `production` |
| `parent_id` | keyword | keyword | Group id. Paraphrases and ASR variants share it, and splits are by group |
| `split` | keyword | keyword | `train`, `val`, `test`, `golden`, `unlabeled` |
| `label_status` | keyword | keyword | `gold`, `silver`, `pending_review`, `rejected` |
| `asr_noisy` | bool | bool | Came through TTS and Whisper |
| `model_confidence`, `margin` | float | no | Classifier output at labeling time |
| `cluster_id` | keyword | keyword | Set by the weekly clustering job |
| `source_doc_id` | keyword | keyword | Lineage for utterances mined from a PDF |
| `consent_training` | bool | bool | Production utterances only |
| `user_hash` | keyword | keyword | Production utterances: deletion on consent withdrawal |
| `tenant_id` | keyword | tenant index | Isolation for production data |
| `dataset_version` | keyword | keyword | Which dataset build includes it |
| `created_at`, `expires_at` | datetime | datetime | Drift windows and retention |
| `embedder_version`, `schema_version` | keyword | no | Guards |

Example point (the seed utterance from TRAINING.md section 3.3):

```json
{
  "id": "2df8988b-a8c1-5ca4-ae04-5a1257046571",
  "vector": {"dense": [0.021, 0.067, -0.015]},
  "payload": {
    "utt_id": "u-00123",
    "text": "how do i create a controller and a service in java",
    "raw_text": "how do i create a controller and a service in java",
    "intent": "CREATE_CODE_ARTIFACT",
    "slots": [{"label": "ARTIFACT", "text": "controller"}, {"label": "ARTIFACT", "text": "service"}, {"label": "LANGUAGE", "text": "java"}],
    "slot_labels": ["ARTIFACT", "LANGUAGE"],
    "source": "seed",
    "parent_id": "u-00123",
    "split": "train",
    "label_status": "gold",
    "asr_noisy": false,
    "dataset_version": "v12",
    "created_at": "2026-10-25T10:00:00Z",
    "embedder_version": "emb_v3",
    "schema_version": 1
  }
}
```

### 5.3 `templates`: routing index for template-first responses

- **Purpose:** find which response template fits a spoken request ("create a REST controller for User"), as the fallback and tie-breaker next to rule-based routing. The template **content** (files, manifests) lives in Git and the template registry, never in Qdrant.
- **Point:** one example utterance or one description of a template. Add 20 to 50 paraphrases per template, including ASR-noisy ones ("controler").
- **Vector:** `dense`. The router takes the best score per `template_id`.

| Field | Type | Indexed | Purpose |
|---|---|---|---|
| `example_id` | keyword | no | Canonical id of this example (`t_spring_rest_crud_001`). The point id is the UUIDv5 of it |
| `template_id` | keyword | keyword | Registry id, for example `spring-boot/rest-crud` |
| `pack_version` | keyword | no | `1.0.0` |
| `kind` | keyword | keyword | `example_utterance` or `description` |
| `text` | string | no | The embedded utterance or description |
| `framework` | keyword | keyword | `spring-boot` |
| `language` | keyword | keyword | `java` |
| `artifact` | keyword | keyword | `controller`, `service`, `repository`, `model`, `crud` |
| `status` | keyword | keyword | `active`, `draft`, `deprecated` |
| `scope` | keyword | keyword | `global` or `tenant` |
| `tenant_id` | keyword | keyword | Only for tenant templates |
| `compat` | object | no | `{"spring_boot": ">=3.2 <5.0", "java": ">=17"}` |
| `origin` | keyword | no | `curated` or `mined_from_feedback` |
| `created_at` | datetime | no | |
| `embedder_version`, `schema_version` | keyword | no | Guards |

Example points:

```json
{
  "points": [
    {
      "id": "e08b0756-8227-5cb2-8f1c-6cf2359627dc",
      "vector": {"dense": [0.044, -0.031, 0.102]},
      "payload": {
        "example_id": "t_spring_rest_crud_001",
        "template_id": "spring-boot/rest-crud",
        "pack_version": "1.0.0",
        "kind": "example_utterance",
        "text": "create a REST controller for User",
        "framework": "spring-boot",
        "language": "java",
        "artifact": "controller",
        "status": "active",
        "scope": "global",
        "compat": {"spring_boot": ">=3.2 <5.0", "java": ">=17"},
        "origin": "curated",
        "created_at": "2026-10-25T10:00:00Z",
        "embedder_version": "emb_v3",
        "schema_version": 1
      }
    }
  ]
}
```

Retrieval caveat: when a user asks for a `controller`, the template's dependency closure (controller, service, repository, model) is decided by the template manifest, not by this index.

### 5.4 `glossary_terms`: semantic lookup of vocabulary

- **Purpose:** map messy speech or typed text to canonical terms (PDF_LEARNING F32, TRAINING.md P3): "dispatcher servlet" finds `DispatcherServlet` even when string matching fails, and review screens find near-duplicate candidates.
- **Point:** one term. **Vector:** `dense` of `canonical + expansion + definition`.
- **Source of truth:** Postgres `glossary` (reviewed). Qdrant holds only approved and pending terms.

| Field | Type | Indexed | Purpose |
|---|---|---|---|
| `term_id` | keyword | no | `term_restcontroller` |
| `canonical` | string | no | `@RestController` |
| `aliases` | keyword[] | keyword | `rest controller`, `restcontroller` |
| `expansion`, `definition` | string | no | `Java Persistence API`, short definition |
| `kind` | keyword | keyword | `identifier`, `acronym`, `concept`, `product` |
| `language`, `framework` | keyword | keyword | Taxonomy |
| `status` | keyword | keyword | `approved`, `pending`, `rejected` |
| `scope` | keyword | keyword | `global`, `tenant`, `user` |
| `tenant_id` | keyword | keyword | Tenant and user scope |
| `source_doc_ids` | keyword[] | keyword | Which PDFs taught the term |
| `stt_hotword` | bool | bool | Feed to the STT prompt |
| `created_at` | datetime | no | |

### 5.5 `semantic_cache`: answers to repeated questions

- **Purpose:** return a stored answer for a near-identical question without retrieval or an LLM call (TRAINING.md P14).
- **Point:** one cached question. **Vector:** `dense`. The answer body lives in Redis under `answer_ref`.
- **Safety rule:** an entry is reusable only by callers with the same `scope_hash`, which is the SHA-256 of tenant, sorted ACL subjects, and document scope. A user who cannot read a document therefore never receives an answer built from it.

| Field | Type | Indexed | Purpose |
|---|---|---|---|
| `cache_id`, `answer_ref` | keyword | no | Entry id and Redis key |
| `question_norm` | string | no | Normalized question |
| `scope_hash` | keyword | keyword | Who may reuse the entry |
| `tenant_id` | keyword | keyword | Sweeps and deletes |
| `index_version` | keyword | keyword | Physical `code_knowledge` collection used |
| `prompt_version` | keyword | keyword | `answer_with_citations@7` |
| `model_versions` | object | no | Intent, reranker, generator versions |
| `depends_on_doc_ids` | keyword[] | keyword | Invalidate on document update or delete |
| `gate` | keyword | no | `answer` only (clarify and abstain are never cached) |
| `created_at`, `expires_at` | datetime | datetime | TTL sweeps |

- **Expiry:** I found no built-in per-point expiry in the docs pages I read (**verify**). Use `expires_at` plus a scheduled delete-by-filter job (section 7).

### 5.6 `user_memory` (v2, opt-in)

- **Purpose:** fuzzy recall of past conversation summaries and stated facts for personalization. Structured preferences (package name, Lombok yes or no, preferred language) belong in Postgres `user_prefs`, not here.
- **Point:** one memory item. **Vector:** `dense`.

| Field | Type | Indexed | Purpose |
|---|---|---|---|
| `memory_id` | keyword | no | |
| `user_hash` | keyword | tenant index | Every query filters on it. The tenant index co-locates each user's points |
| `kind` | keyword | keyword | `conversation_summary`, `fact` |
| `text` | string | no | PII-scrubbed |
| `source_trace_id` | keyword | no | Link to the decision trace |
| `importance` | float | no | Ranking |
| `consent` | bool | bool | Must be true |
| `created_at`, `expires_at` | datetime | datetime | Retention |

Deletion on request is one filter: `user_hash = ...`.

### 5.7 `page_regions` (v2, optional)

- **Purpose:** retrieve pages by their image for figure-heavy PDFs, using a ColPali-style model that produces many small vectors per page (experimental, needs a GPU). The collection uses the multivector option with the `max_sim` comparator.

```json
{
  "vectors": {
    "pages": {
      "size": 128,
      "distance": "Cosine",
      "multivector_config": {"comparator": "max_sim"}
    }
  },
  "metadata": {"embedder_version": "colpali_v1", "schema_version": 1, "purpose": "page_regions"}
}
```

`size` is the model's per-patch dimension (128 in the Qdrant docs example). Check your model. Payload: `doc_id`, `page_index`, `tenant_id`, `acl`, `thumb_ref`. The multivector size limit (`number_of_sub_vectors * vector_size` under 1,048,576) is documented and not configurable.

---

## 6. Creating collections and indexes

**Order matters:** (1) create the collection, (2) create the payload indexes, (3) load data.

### 6.1 Create `code_knowledge`

```json
{
  "vectors": {
    "dense": {"size": 768, "distance": "Cosine"}
  },
  "sparse_vectors": {"sparse": {}},
  "hnsw_config": {"m": 16, "ef_construct": 100},
  "quantization_config": {"scalar": {"type": "int8", "quantile": 0.99, "memory": "pinned"}},
  "shard_number": 6,
  "replication_factor": 2,
  "metadata": {"embedder_version": "emb_v3", "schema_version": 1, "purpose": "code_knowledge"}
}
```

`PUT /collections/code_knowledge__emb_v3__s1`

- `768` is an example. Use your embedder's dimension.
- `shard_number: 6` with `replication_factor: 2` suits a 3-node cluster (a multiple of the node count, at least 2 shards per node). For a single development node use `1` and `1`. **The shard count cannot be changed on a self-hosted cluster without recreating the collection**, which is one more reason the blue/green migration in section 14 exists.
- Memory placement is **version-sensitive.** Qdrant 1.19 introduced one `memory` parameter (`pinned`, `cached`, `cold`) and deprecated the older `on_disk`, `always_ram`, and `on_disk_payload` flags, which still work. On servers older than 1.19 write `"always_ram": true` instead of `"memory": "pinned"`. Do not mix schemas from two versions: read the docs for the server you run.

| Feature | Needs Qdrant | Note |
|---|---|---|
| Hybrid queries (`prefetch`, fusion) | 1.10+ | DBSF from 1.11, RRF `k` from 1.16, weighted RRF from 1.17 |
| Multivectors (`max_sim`) | 1.10+ | `page_regions` |
| Tenant index (`is_tenant`) | 1.11+ | |
| Collection `metadata` | 1.16+ | Older servers: rely on the Postgres registry for the embedder guard |
| ACORN search for strict filters | 1.16+ | Consider it if recall drops under very selective filters |
| Unified `memory` tiers | 1.19+ | Replaces `on_disk`, `always_ram`, `on_disk_payload` |

### 6.2 Payload indexes for `code_knowledge`

One `PUT /collections/{name}/index` request per entry:

```json
[
  {"field_name": "tenant_id", "field_schema": {"type": "keyword", "is_tenant": true}},
  {"field_name": "acl", "field_schema": "keyword"},
  {"field_name": "doc_id", "field_schema": "keyword"},
  {"field_name": "doc_version", "field_schema": "integer"},
  {"field_name": "is_latest", "field_schema": "bool"},
  {"field_name": "is_generated", "field_schema": "bool"},
  {"field_name": "source_type", "field_schema": "keyword"},
  {"field_name": "chunk_type", "field_schema": "keyword"},
  {"field_name": "language", "field_schema": "keyword"},
  {"field_name": "natural_language", "field_schema": "keyword"},
  {"field_name": "framework", "field_schema": "keyword"},
  {"field_name": "artifact_type", "field_schema": "keyword"},
  {"field_name": "topic_tags", "field_schema": "keyword"},
  {"field_name": "page_start", "field_schema": {"type": "integer", "lookup": false, "range": true}},
  {"field_name": "page_end", "field_schema": {"type": "integer", "lookup": false, "range": true}},
  {"field_name": "created_at", "field_schema": "datetime"}
]
```

- Every field here appears in a filter somewhere in section 7 or in a feature (PDF_LEARNING F24, F30 scope, F38 freshness). A field that is never filtered gets no index, because every index costs memory and write time.
- `page_start` and `page_end` are range-only (`lookup: false`) because they are only used for "pages 40 to 60".
- Other collections follow the "Indexed" columns in section 5. The `utterances` and `user_memory` collections use `tenant_id` and `user_hash` as tenant indexes.
- **Startup assertion:** each service reads the collection info and fails the deploy if a field used in its filters has no payload index (section 13).

### 6.3 Upsert a chunk

`PUT /collections/code_knowledge/points?wait=true` (the point id is the UUIDv5 of `c_5f3a`; vectors are shortened here, real ones have 768 floats):

```json
{
  "points": [
    {
      "id": "60e3ad15-bb14-518d-869a-6027cba4ccdc",
      "vector": {
        "dense": [0.012, -0.044, 0.093],
        "sparse": {"indices": [101, 2048, 77], "values": [0.9, 0.4, 0.2]}
      },
      "payload": {
        "chunk_id": "c_5f3a",
        "tenant_id": "acme",
        "acl": ["user:u_7c1d"],
        "doc_id": "d_91e2",
        "doc_version": 1,
        "is_latest": true,
        "source_type": "pdf",
        "chunk_type": "code",
        "language": "java",
        "natural_language": "en",
        "framework": "spring-boot",
        "framework_version": "3.5",
        "artifact_type": "controller",
        "topic_tags": ["rest", "dependency-injection"],
        "text": "@RestController\npublic class UserController {\n    private final UserService service;\n}",
        "context_header": "Spring Boot Guide > Web > Creating a REST Controller",
        "section_path": ["Web", "Creating a REST Controller"],
        "parent_id": "p_77aa",
        "page_start": 42,
        "page_end": 42,
        "page_label": "42",
        "bbox": [[42, 72, 200, 540, 330]],
        "title": "Spring Boot Guide",
        "license": "user_supplied",
        "quality_score": 0.5,
        "ocr_confidence": null,
        "is_generated": false,
        "text_hash": "sha256:9a1f",
        "created_at": "2026-10-25T10:00:00Z",
        "valid_from": "2026-10-25T10:00:00Z",
        "valid_to": null,
        "embedder_version": "emb_v3",
        "pipeline_version": "pdf-ingest@1.4.0",
        "schema_version": 1
      }
    }
  ]
}
```

Use batches of 64 to 256 points per request and the Python client's `upload_points` helper, which parallelizes and retries. Pass `wait=true` on the last batch of an ingestion so the document is searchable when its status becomes `ready`.

### 6.4 Payload updates and deletes

- **Payload-only change** (for example the nightly `quality_score` sync). Do not re-upsert, which would replace vectors. Use payload operations:

`POST /collections/code_knowledge/points/batch` (**verify** the path on your version; the `set_payload` operation shape is from the docs):

```json
{
  "operations": [
    {"set_payload": {"payload": {"quality_score": 0.82}, "points": ["60e3ad15-bb14-518d-869a-6027cba4ccdc"]}}
  ]
}
```

- **Delete a document version** (`POST /collections/code_knowledge/points/delete`):

```json
{
  "filter": {
    "must": [
      {"key": "doc_id", "match": {"value": "d_91e2"}},
      {"key": "doc_version", "match": {"value": 1}}
    ]
  }
}
```

- **Supersede a version:** set `is_latest` to `false` and `valid_to` on the old points, in the same transaction that marks the new version `ready`.

| Operation | Request |
|---|---|
| Create collection | `PUT /collections/{name}` |
| Create payload index | `PUT /collections/{name}/index` |
| Upsert points | `PUT /collections/{name}/points?wait=true` |
| Query (hybrid, kNN) | `POST /collections/{name}/points/query` |
| Delete by filter | `POST /collections/{name}/points/delete` |
| Switch aliases (atomic) | `POST /collections/aliases` |
| Collection info (metadata, payload schema) | `GET /collections/{name}` |
| Snapshot (create, list) | `POST` and `GET /collections/{name}/snapshots` |
| Restore snapshot | `PUT /collections/{name}/snapshots/recover` |

---

## 7. Query catalog

| Query | Collection | Vector | Filter | Returns | Consumer |
|---|---|---|---|---|---|
| Ask (hybrid) | `code_knowledge` | `dense` + `sparse`, RRF | Mandatory filter (tenant, ACL, latest, scope) | Top 20 chunks for the reranker | `AskQuestion`, PDF_LEARNING F24 |
| Cache lookup | `semantic_cache` | `dense`, `score_threshold` | `scope_hash`, `index_version`, `prompt_version`, not expired | One `answer_ref` or nothing | TRAINING.md P14 |
| Template routing | `templates` | `dense` | `status=active`, `framework`, `language` when known | Top 5 template ids with scores | Template router |
| Glossary lookup | `glossary_terms` | `dense` | `status=approved`, scope | Canonical terms for correction and expansion | TRAINING.md P3 |
| Hard negatives | `code_knowledge` | `dense` | Tenant, latest, `must_not` positives by `has_id` | Ranks 5 to 30 as candidates | Embedder and reranker training |
| Round trip | `code_knowledge` | `dense` | Same scope as the source document | Rank of the source chunk | PDF_LEARNING F33 |
| Leakage check | `utterances` | `dense`, `score_threshold` | `split=train` | Near-duplicates of a test utterance | CI data tests |
| kNN intent vote | `utterances` | `dense` | `label_status=gold` | Labels and similarities of neighbors | Confidence gate second opinion |
| Memory recall | `user_memory` | `dense` | `user_hash`, `consent`, not expired | Top 3 memories | Personalization |

### 7.1 Ask: hybrid dense + sparse with RRF

`POST /collections/code_knowledge__emb_v3__s1/points/query`. The mandatory filter is repeated inside **every** `prefetch` entry. The docs do not say how a top-level filter interacts with prefetch results (**verify**), so the adapter never relies on it, and the isolation contract test in section 13 proves the behavior against a real server.

```json
{
  "prefetch": [
    {
      "query": [0.012, -0.044, 0.093],
      "using": "dense",
      "filter": {"must": [
        {"key": "tenant_id", "match": {"value": "acme"}},
        {"key": "acl", "match": {"any": ["user:u_7c1d", "team:platform"]}},
        {"key": "is_latest", "match": {"value": true}},
        {"key": "doc_id", "match": {"any": ["d_91e2"]}}
      ]},
      "limit": 50
    },
    {
      "query": {"indices": [101, 2048, 77], "values": [0.9, 0.4, 0.2]},
      "using": "sparse",
      "filter": {"must": [
        {"key": "tenant_id", "match": {"value": "acme"}},
        {"key": "acl", "match": {"any": ["user:u_7c1d", "team:platform"]}},
        {"key": "is_latest", "match": {"value": true}},
        {"key": "doc_id", "match": {"any": ["d_91e2"]}}
      ]},
      "limit": 50
    }
  ],
  "query": {"rrf": {}},
  "limit": 20,
  "with_payload": {"include": ["chunk_id", "doc_id", "text", "page_start", "bbox", "section_path"]}
}
```

This body is exactly what `hybrid_query` in section 12 builds. On servers older than 1.16 the RRF form may be `{"fusion": "rrf"}` (**verify**). Search-time tuning goes in `params`, for example `{"hnsw_ef": 128, "quantization": {"rescore": true, "oversampling": 2.0}}`.

When the scope is a single document, the filtered set is small. Qdrant uses a full scan instead of the HNSW graph when the estimated number of matching points is below `full_scan_threshold` (default 10,000 KB of vectors), so document-scoped questions are effectively exact.

### 7.2 Cache lookup

```json
{
  "query": [0.011, -0.040, 0.090],
  "using": "dense",
  "filter": {"must": [
    {"key": "scope_hash", "match": {"value": "9b1c0f"}},
    {"key": "index_version", "match": {"value": "code_knowledge__emb_v3__s1"}},
    {"key": "prompt_version", "match": {"value": "answer_with_citations@7"}},
    {"key": "expires_at", "range": {"gt": "2026-10-25T10:00:00Z"}}
  ]},
  "score_threshold": 0.95,
  "limit": 1,
  "with_payload": {"include": ["answer_ref", "depends_on_doc_ids"]}
}
```

The 0.95 threshold is a starting point: tune it on real pairs of questions that should and should not share an answer.

### 7.3 Template routing

```json
{
  "query": [0.044, -0.031, 0.102],
  "using": "dense",
  "filter": {"must": [
    {"key": "status", "match": {"value": "active"}},
    {"key": "framework", "match": {"value": "spring-boot"}},
    {"key": "language", "match": {"value": "java"}}
  ]},
  "limit": 5,
  "with_payload": {"include": ["template_id", "pack_version", "artifact", "kind", "text"]}
}
```

The router groups hits by `template_id`, takes each group's best score, and combines that with rule-based matches. Below a confidence threshold it falls back to retrieval-augmented generation.

### 7.4 Hard negatives for training

Run by the training job under a service identity that reads only tenants with training consent. The known positive is excluded by point id.

```json
{
  "query": [0.03, 0.12, -0.08],
  "using": "dense",
  "filter": {
    "must": [
      {"key": "tenant_id", "match": {"value": "acme"}},
      {"key": "is_latest", "match": {"value": true}}
    ],
    "must_not": [
      {"has_id": ["60e3ad15-bb14-518d-869a-6027cba4ccdc"]}
    ]
  },
  "limit": 30,
  "with_payload": {"include": ["chunk_id", "framework", "language", "doc_id"]}
}
```

Keep ranks 5 to 30 as candidates, then drop false negatives (chunks that actually answer the question) by reviewer or rule before using them (TRAINING.md section 4.2).

### 7.5 Leakage check between golden and training data

```json
{
  "query": [0.05, -0.02, 0.07],
  "using": "dense",
  "filter": {"must": [{"key": "split", "match": {"value": "train"}}]},
  "score_threshold": 0.92,
  "limit": 3,
  "with_payload": {"include": ["utt_id", "text", "intent"]}
}
```

Any hit fails the data test. The 0.92 threshold is a starting point.

### 7.6 Cache expiry sweep

`POST /collections/semantic_cache__emb_v3__s1/points/delete`, run every few minutes:

```json
{"filter": {"must": [{"key": "expires_at", "range": {"lt": "2026-10-25T10:00:00Z"}}]}}
```

---

## 8. How the vector database serves training and learning

| # | Workflow | Collections | Operation | Output | Used by |
|---|---|---|---|---|---|
| 1 | Hard-negative mining | `code_knowledge` | Search each training query, exclude positives, take ranks 5 to 30 | Candidate negatives | Embedder and reranker training (TRAINING.md 4.2, 4.3) |
| 2 | Round-trip filter for synthetic questions | `code_knowledge` | Search the generated question, keep it if its source chunk is in the top 5 | Kept and discarded questions, retrieval-gap report | PDF_LEARNING F33 |
| 3 | Near-duplicate removal | `utterances`, `code_knowledge` | Nearest neighbor above about 0.95 within the same intent or document family | Duplicate groups to drop | Dataset builds, ingestion |
| 4 | Leakage detection | `utterances` | Each golden or test vector against `split=train` above about 0.92 | Pass or fail with offending pairs | CI data tests (TRAINING.md 11) |
| 5 | Label-noise detection | `utterances` | For each labeled item, 10 neighbors vote, compare with its own label | Items that disagree with the neighbor majority | Review queue (TRAINING.md 7.5) |
| 6 | Active learning: diversity and novelty | `utterances` | Cluster production vectors (`cluster_id`), sample per cluster, rank by low similarity to labeled data | Ranked review queue | TRAINING.md 7.3 |
| 7 | kNN intent fallback | `utterances` | Nearest gold neighbors when classifier confidence is low | Second opinion for the gate | TRAINING.md P2 |
| 8 | Template routing | `templates` | Search by utterance | Candidate template ids | TEMPLATE_RESPONSES.md |
| 9 | Drift monitoring | `utterances` | Weekly: mean nearest-neighbor similarity of recent production queries, share under 0.6, centroid shift versus a reference week | Alarm when thresholds are crossed | TRAINING.md 7.5 |
| 10 | Lineage and deletion | all | Delete or flag by `doc_id`, `source_doc_id`, `depends_on_doc_ids`, `user_hash` | Purged derived data, flagged dataset versions | PDF_LEARNING F39, F41 |
| 11 | Re-embedding after an embedder change | all vector collections | Rebuild from Postgres and DVC, evaluate, promote | New live collections | TRAINING.md P8, section 14 |
| 12 | Retrieval evaluation | `code_knowledge` | Run golden queries on the candidate collection. Compare approximate results with exact search (`exact: true`) for ground truth | recall@k, MRR, nDCG, ANN recall | Promotion gates |

All thresholds (0.95, 0.92, 0.6, k = 10) are starting points to tune on your data.

**One training cycle, end to end**

1. A user votes thumbs-down with reason `wrong_language`. The event lands in Postgres (PDF_LEARNING F37).
2. The nightly job mines hard negatives from `code_knowledge` (workflow 1), runs the round-trip filter on synthetic questions (workflow 2), and deduplicates and leak-checks the new dataset version (workflows 3 and 4).
3. The training job fine-tunes the embedder to `emb_v4` (TRAINING.md 4.2) and registers it.
4. The reindex job builds `code_knowledge__emb_v4__s1`, plus new `templates`, `utterances`, `glossary_terms`, and an empty `semantic_cache` for `emb_v4` (workflow 11).
5. Gates run: recall@5, MRR, per-slice no-regression, ANN recall, latency (workflow 12).
6. `emb_v4` goes to shadow, then canary traffic. Pods using `emb_v4` resolve the `emb_v4` collections automatically (section 4).
7. After full rollout, the `emb_v3` collections are retired and later deleted. Nothing was edited in place, and rollback is a registry change.

---

## 9. Multi-tenancy, access control, and security

- **Tenant model.** A shared collection with `tenant_id` as a **tenant index** (`is_tenant: true`, Qdrant 1.11+), which co-locates each tenant's vectors. For a few large tenants, Qdrant also offers user-defined sharding, and tiered multitenancy combines both. Dedicated collections only for strict isolation (each collection has its own overhead, and Qdrant Cloud caps a cluster at 1,000 collections by default).
- **Access control model.** Each chunk lists the subjects that may read it in `acl`. A subject is `user:`, `team:`, `tenant:`, or `public`. The caller's subjects come from the access token, never from the request body.
- **Enforced in the adapter, fail closed.** `mandatory_filter` raises `PermissionError` if the tenant or subjects are missing. The filter is repeated in every `prefetch`. Clients never talk to Qdrant.
- **Changing access.** Sharing or unsharing a document is a payload update on all its points, selected by `doc_id`. Invalidate related `semantic_cache` entries through `depends_on_doc_ids`.
- **Service identities.** Qdrant supports an admin API key and a read-only API key (`service.api_key`, `service.read_only_api_key`, or the environment variables `QDRANT__SERVICE__API_KEY` and `QDRANT__SERVICE__READ_ONLY_API_KEY`), sent in the `api-key` header. The admin key can be rotated without downtime by temporarily setting `alt_api_key`.
- **Least privilege with JWT roles.** With `service.jwt_rbac: true`, tokens (HS256, signed with the API key) carry per-collection `r` or `rw` claims and an expiry. Example: retrieval gets `r` on `code_knowledge`, ingestion gets `rw`. Test whether claims match **aliases or physical names** on your version before relying on it (**verify**).
- **Network.** Bind or expose only what is needed, use TLS (`service.enable_tls`), and keep the internal cluster port 6335 reachable only between Qdrant pods. Use a Kubernetes `NetworkPolicy` so that only the gateway, retrieval, ingestion, and training pods reach ports 6333 and 6334. Run as non-root with a read-only root filesystem.
- **Vectors are sensitive.** Embeddings can leak information about the text they encode, so treat them like the text. Scrub PII and secrets before embedding transcripts and memories, and use encrypted volumes.
- **Deletion.** Deletes are logical at once and physical when Qdrant optimizes segments. If compliance needs a physical-deletion deadline, agree it with your compliance team and test it.
- **Consent.** `utterances` and `user_memory` store only items with consent flags, and withdrawal deletes by `user_hash`.

---

## 10. Performance, memory, and sizing

**Index settings**

| Setting | Default | Our starting choice | Note |
|---|---|---|---|
| HNSW `m` | 16 | 16 | Higher is more accurate and larger |
| HNSW `ef_construct` | 100 | 100 | Raise only if the recall test says so |
| Search `hnsw_ef` | `ef_construct` | 64 to 128 | Tune per query class |
| `full_scan_threshold` | 10,000 KB | default | Small filtered sets are scanned exactly |
| Quantization | none | Scalar int8, `quantile` 0.99 | About 4x less memory for the quantized copy, usually under 1% error according to the docs |
| Search-time quantization | | `rescore: true`, `oversampling: 2.0` | Rescoring with original vectors recovers accuracy |
| Dense `datatype` | float32 | float32 | `float16` halves dense storage with virtually no search-quality impact per the docs. Test first |

- **Binary quantization** (about 32x) only for high-dimensional, centered embeddings and always with rescoring. **Product quantization** (up to 64x) when memory is the top priority and some accuracy loss is acceptable. Decide with the recall test, not by default.
- **Memory tiers (Qdrant 1.19+).** `pinned` keeps data in memory and never evicts it. `cached` is memory-mapped and pre-warmed. `cold` is memory-mapped on first use. Dense vectors and payloads cannot be pinned.

| Component | Recommended tier for `code_knowledge` | Reason |
|---|---|---|
| Quantized vectors | `pinned` | Every search touches them |
| Original dense vectors | on disk (OS cache) | Only needed for rescoring |
| HNSW graph | `cached` | Hot but evictable |
| Payload | `cached` | Needed for the returned top-k only |
| Sparse index | `pinned` (default) | Hybrid search uses it on every query |
| Payload and vectors of `utterances`, `user_memory` | `cold` | Used in batch jobs, not on the request path |

These tiers are a starting point. Qdrant's docs note that not every structure supports every tier, so check what your server version allows for each component.

- **Create payload indexes first** so the filterable HNSW graph gets its extra edges. Strict filters can still disconnect parts of the graph. If recall drops under very selective filters, consider ACORN (Qdrant 1.16+).
- **Measure ANN recall** by running the golden queries with `"params": {"exact": true}` as ground truth and comparing with the approximate results. Gate promotions on it.

**Sizing (illustrative, back-of-envelope; measure on real data).** Assumptions: 768 dimensions, float32 originals, int8 quantized copy, 100 non-zero values per sparse vector (8 bytes each), 2.5 KB payload, HNSW `m = 16` with 4-byte links on layer 0 only.

| Points | Original dense | Quantized copy | Sparse | HNSW links | Payload | Disk, all structures | RAM to pin the quantized copy |
|---|---|---|---|---|---|---|---|
| 100,000 | 0.29 GB | 0.07 GB | 0.07 GB | 0.01 GB | 0.24 GB | about 0.7 GB | about 0.07 GB |
| 1,000,000 | 2.86 GB | 0.72 GB | 0.75 GB | 0.12 GB | 2.38 GB | about 6.8 GB | about 0.72 GB |
| 10,000,000 | 28.61 GB | 7.15 GB | 7.45 GB | 1.19 GB | 23.84 GB | about 68 GB | about 7.2 GB |

Add headroom for the graph cache, OS page cache, and replication (`replication_factor: 2` doubles disk). A chunk is about 350 tokens, so a 120-page technical PDF typically yields a few hundred chunks. Count your own.

---

## 11. Operations on Kubernetes

- **Topologies**
  - Development: Docker Compose, one node, `shard_number: 1`, `replication_factor: 1`.
  - Staging: one node, daily snapshots.
  - Production: 3-node StatefulSet with `cluster.enabled: true`, `replication_factor: 2`, 6 shards per collection (or 12 shards if you expect to grow to 6 or 12 nodes: the docs note 12 shards scale across 1, 2, 3, 6, or 12 nodes).
- **Deployment.** The official Qdrant Helm chart or your own StatefulSet. Use SSD persistent volumes, pod anti-affinity across nodes, a PodDisruptionBudget (`maxUnavailable: 1`), readiness and liveness probes, resource requests sized from section 10, and Secrets for keys. The Helm chart and its values were not checked in this session, so check its current values file.
- **Qdrant configuration (excerpt).** Keys come from the docs. Secrets come from environment variables, not this file.

```yaml
service:
  jwt_rbac: true
  enable_tls: true
cluster:
  enabled: true
storage:
  snapshots_config:
    snapshots_storage: s3
    s3_config:
      bucket: qdrant-snapshots
      region: us-east-1
      endpoint_url: http://minio.platform.svc:9000
```

- **Backups**
  - Collection snapshots (`POST /collections/{name}/snapshots`), taken **on each node** because a snapshot contains only the data of the node that created it, stored in MinIO through the S3 snapshot configuration.
  - Take one before every promotion or alias flip. Keep 7 daily and 4 weekly.
  - Collection snapshots do not include aliases, so the alias map is restored from the Postgres registry.
  - A snapshot can only be restored to the same minor version or the next one.
  - Full-storage snapshots are for single-node deployments only.
  - Second line of defense: rebuild from Postgres. Measure the rebuild time and write it in the runbook.
  - Restore drill into staging once a month.
- **Monitoring.** Scrape the Prometheus `/metrics` endpoint. Dashboards: points per collection versus `points_expected`, indexed versus total vectors, p95 query latency by endpoint, RAM and disk, optimizer activity. Alerts: latency, disk above 80%, a collection without a live registry row, and replicas out of sync. Check the metric names on your version.
- **Upgrades.** One minor version at a time, rolling, with `replication_factor` of at least 2 and a snapshot taken first.
- **Scaling.** Shard counts are fixed at creation on self-hosted clusters. Pick a shard count that is a multiple of your target node counts, or change it through a blue/green rebuild.

---

## 12. Ports, adapters, and code

The ports follow the interface-segregation split in FEATURE.md: ingestion needs only the writer, the query path only the searcher.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Point:
    canonical_id: str          # chunk_id, utt_id, term_id ... the point id is derived from it
    vectors: dict              # {"dense": [...], "sparse": {"indices": [...], "values": [...]}}
    payload: dict

@dataclass(frozen=True)
class Hit:
    canonical_id: str
    score: float
    payload: dict

class VectorWriter(ABC):
    @abstractmethod
    def upsert(self, collection: str, points: list) -> None: ...
    @abstractmethod
    def set_payload(self, collection: str, canonical_ids: list, payload: dict) -> None: ...
    @abstractmethod
    def delete_where(self, collection: str, flt: dict) -> None: ...

class VectorSearcher(ABC):
    @abstractmethod
    def hybrid_search(self, collection: str, dense: list, sparse: dict, scope: "Scope", limit: int = 20) -> list: ...
    @abstractmethod
    def nearest(self, collection: str, dense: list, flt: dict, limit: int = 10,
                score_threshold: Optional[float] = None) -> list: ...
```

Deterministic ids and versioned names:

```python
import re
import uuid

POINT_NAMESPACE = uuid.UUID("6f1d3b9e-0b8a-4c55-9d52-3c2f5f6a7b11")   # fixed forever: changing it changes every point id

def point_id(canonical_id: str) -> str:
    """Deterministic Qdrant point id from the canonical id (chunk, utterance, term, ...)."""
    return str(uuid.uuid5(POINT_NAMESPACE, canonical_id))

_NAME = re.compile(r"^(?P<purpose>[a-z_]+)__(?P<embedder>[a-z0-9_]+)__s(?P<schema>\d+)$")

def collection_name(purpose: str, embedder: str, schema: int) -> str:
    return f"{purpose}__{embedder}__s{schema}"

def parse_collection_name(name: str) -> dict:
    match = _NAME.match(name)
    if not match:
        raise ValueError(f"not a versioned collection name: {name}")
    return {"purpose": match["purpose"], "embedder": match["embedder"], "schema": int(match["schema"])}
```

Mandatory scope filter and the hybrid query body (fail closed, filter repeated in every prefetch):

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Scope:
    tenant_id: str
    subjects: tuple                      # the caller's ACL subjects, e.g. ("user:u_7c1d", "team:platform")
    doc_ids: tuple = ()
    latest_only: bool = True

def mandatory_filter(scope: Scope) -> dict:
    """The filter every query on code_knowledge must carry. Fails closed."""
    if not scope.tenant_id or not scope.subjects:
        raise PermissionError("a query needs a tenant and at least one ACL subject")
    must = [
        {"key": "tenant_id", "match": {"value": scope.tenant_id}},
        {"key": "acl", "match": {"any": list(scope.subjects)}},
    ]
    if scope.latest_only:
        must.append({"key": "is_latest", "match": {"value": True}})
    if scope.doc_ids:
        must.append({"key": "doc_id", "match": {"any": list(scope.doc_ids)}})
    return {"must": must}

def hybrid_query(dense, sparse, scope: Scope, *, prefetch_limit: int = 50, limit: int = 20,
                 extra_conditions=()) -> dict:
    """Request body for POST /collections/code_knowledge/points/query (dense + sparse, RRF)."""
    flt = {"must": mandatory_filter(scope)["must"] + list(extra_conditions)}
    return {
        "prefetch": [
            {"query": dense, "using": "dense", "filter": flt, "limit": prefetch_limit},
            {"query": sparse, "using": "sparse", "filter": flt, "limit": prefetch_limit},
        ],
        "query": {"rrf": {}},
        "limit": limit,
        "with_payload": {"include": ["chunk_id", "doc_id", "text", "page_start", "bbox", "section_path"]},
    }
```

Resolution, alias switching, and the embedder guard:

```python
def resolve_collection(registry_rows: list, purpose: str, embedder_version: str) -> str:
    """Pick the live collection built with the same embedder that produced the query vector.
    `registry_rows` are rows of the Postgres index_registry table."""
    live = [row["collection"] for row in registry_rows
            if row["purpose"] == purpose
            and row["embedder_version"] == embedder_version
            and row["status"] == "live"]
    if len(live) != 1:
        raise LookupError(f"expected exactly one live {purpose} collection for {embedder_version}, found {len(live)}")
    return live[0]

def alias_switch_request(alias: str, new_collection: str) -> dict:
    """One atomic request: the alias never points nowhere."""
    return {"actions": [
        {"delete_alias": {"alias_name": alias}},
        {"create_alias": {"collection_name": new_collection, "alias_name": alias}},
    ]}

def assert_embedder_matches(collection_info: dict, expected: str) -> None:
    """`collection_info` is the "result" object of GET /collections/{name} (metadata needs Qdrant 1.16+)."""
    actual = ((collection_info.get("config") or {}).get("metadata") or {}).get("embedder_version")
    if actual != expected:
        raise RuntimeError(f"collection was built with {actual!r}, this service embeds with {expected!r}")
```

Back-of-envelope sizing (the numbers in section 10 come from this function):

```python
def estimate_gb(points: int, dim: int = 768, dense_bytes: int = 4, sparse_nnz: int = 100,
                payload_kb: float = 2.5, m: int = 16, quantized_bytes: int = 1) -> dict:
    gb = 1024 ** 3
    return {
        "dense_vectors": points * dim * dense_bytes / gb,
        "quantized_copy": points * dim * quantized_bytes / gb,
        "sparse_vectors": points * sparse_nnz * 8 / gb,          # u32 index + f32 value per non-zero
        "hnsw_links": points * 2 * m * 4 / gb,                   # rule of thumb: layer 0 only, 4-byte links
        "payload": points * payload_kb * 1024 / gb,
    }
```

---

## 13. Testing (TDD)

Write these tests first. Most run against an in-memory fake that implements the same ports. The marked ones must also run against a real Qdrant container in CI (for example with Testcontainers), because they check server behavior.

| Test | Level | What it proves |
|---|---|---|
| Point ids are deterministic and valid UUIDs | Unit | Idempotent ingestion |
| Collection names round-trip and bad names are rejected | Unit | Naming contract |
| The filter fails closed without tenant or ACL | Unit | Security default |
| Every `prefetch` repeats the mandatory filter | Unit | No unfiltered candidate set |
| A query vector selects the collection built with the same embedder | Unit | Cutover race removed |
| Resolution fails loudly with zero or two live collections | Unit | Registry integrity |
| Alias switch is one request with two actions | Unit | Atomic flip |
| An embedder mismatch is refused | Unit | Never compare vectors across models |
| Tenant and ACL isolation under a hybrid query | **Real server** | Resolves the **verify** on filters inside `prefetch` |
| Result scores are sorted and `limit` is honored | **Real server** | Port contract (Liskov) |
| Upserting the same id twice leaves one point | **Real server** | Idempotency |
| Re-upserting a point with only `dense` empties its `sparse` vector | **Real server** | Documents the replace behavior |
| Delete by filter removes every point of a document version | **Real server** | Deletion and lineage |
| A concurrent reader never fails while the alias switches | **Real server** | Atomic alias |
| Every field used in a filter has a payload index (read from collection info) | **Real server** | Startup assertion, no silent full scans |
| Approximate recall against `exact: true` stays above the gate | **Real server** | Index configuration regression |
| A read-only token cannot write | **Real server** | JWT roles. Includes the alias versus physical name check |
| Snapshot restore into staging reproduces point counts | Drill | Backup validity |

```python
def test_user_cannot_retrieve_another_users_chunks(store, embedder):
    store.upsert("code_knowledge__emb_v3__s1", [chunk_for(owner="user:alice", text="alice private design notes")])
    scope = Scope("acme", ("user:bob",))
    hits = store.hybrid_search("code_knowledge__emb_v3__s1", embedder.embed("design notes"), {"indices": [], "values": []}, scope)
    assert hits == []
```

(The fixtures `store`, `embedder`, and `chunk_for` are illustrative.)

The unit tests marked above are implemented in the helper module that these snippets come from, and all of them passed when run.

---

## 14. Migration playbook

Two cases use the same machinery.

- **Case A: the embedder changes** (fine-tuned or new model). New vectors, so a new collection per embedding-bearing purpose. Roll out by embedder version (section 4).
- **Case B: the schema or shard count changes, same embedder.** Build the new collection, verify, then switch the alias and the registry in one step.

Steps:

1. **Register.** Insert an `index_registry` row with status `building`. Create the physical collection with its `metadata`, then create all payload indexes **before loading data**.
2. **Dual-write.** Ingestion writes to every collection whose registry status is `building` or `live`, so nothing is lost during the backfill.
3. **Backfill.** The reindex job streams `chunks` from Postgres in keyset-paginated batches (64 to 256 points), re-embeds with the target embedder through TF Serving, and upserts with deterministic ids. It is resumable and safe to re-run. Do the same for `templates`, `utterances`, and `glossary_terms`. Start `semantic_cache` empty.
4. **Verify.** Point counts equal `points_expected` after the dual-write catches up. Golden retrieval gates pass (recall@5, MRR, no slice regression against the champion). ANN recall against exact search is above the gate. p95 latency fits the budget.
5. **Shadow.** Replay a sample of live queries against the candidate and compare overlap and answers (TRAINING.md P16). Status `shadow`.
6. **Canary.** For Case A, route a small share of traffic to pods using the new embedder. They resolve the new collections automatically. For Case B, flip a test tenant first.
7. **Promote.** In one Postgres transaction set the new row to `live` and the old row to `retired`. For Case B also send the alias switch request. Take a snapshot of the old collection first.
8. **Retire.** Keep the old collection read-only for 7 to 14 days, then delete it. Rolling back during that window is one registry change.
9. **Record.** Store the final metrics in the registry row and link the model card.

Alias switch request (`POST /collections/aliases`):

```json
{
  "actions": [
    {"delete_alias": {"alias_name": "code_knowledge"}},
    {"create_alias": {"collection_name": "code_knowledge__emb_v4__s1", "alias_name": "code_knowledge"}}
  ]
}
```

---

## 15. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Query vector compared with vectors from another model | Resolution by embedder version, collection metadata guard, contract tests |
| Cross-tenant or cross-user leak | Fail-closed mandatory filter in every prefetch, tenant index, isolation test on a real server, JWT roles |
| A cached answer reveals a private document | `scope_hash` in the cache key, `depends_on_doc_ids` invalidation, only `answer` outcomes cached |
| Full scans because a filter field has no index | Startup assertion on collection info, indexes created before ingestion |
| Payload bloat and slow writes | Lean payload, parents in Postgres, index only filtered fields |
| Hot updates (feedback counters) degrade the index | Aggregate in Postgres, sync `quality_score` in batches through payload operations |
| Re-upsert silently drops vectors | Payload-only changes use payload operations, a test documents the replace behavior |
| Shard count is wrong and cannot change | Pick a multiple of target node counts, blue/green rebuild as the escape hatch |
| Snapshot cannot be restored after an upgrade | Restore only to the same or next minor version, monthly restore drill, rebuild from Postgres |
| Config differs between Qdrant versions (memory tiers versus `on_disk`) | Pin the server version, read the docs for that version, keep version notes in the runbook |
| Deleted data lingers (derived datasets, caches, trained weights) | Lineage fields, delete cascades, dataset flags, opt-in only training (PDF_LEARNING F39) |
| PII in transcripts and memories | Scrub before embedding, consent flags, short retention, deletion by `user_hash` |
| Embedding drift as users and documents change | Weekly drift job on `utterances`, retrain triggers (TRAINING.md 7.5) |
| Quantization hurts recall | Measure recall before and after, rescoring with oversampling, keep original vectors |

## 16. Roadmap

| Phase | Scope | Exit criteria |
|---|---|---|
| 1 (MVP) | Postgres `index_registry`, `code_knowledge` with `dense` vectors, payload indexes, tenant and ACL filter, deterministic ids, delete by filter, in-memory fake and unit tests | Isolation and idempotency tests green on a real server |
| 2 | `sparse` vectors and hybrid RRF, `templates` routing index, `semantic_cache`, snapshots to MinIO, Prometheus dashboards | Hybrid recall gate green, restore drill passed |
| 3 | `utterances` hygiene (dedupe, leakage, label noise), `glossary_terms`, kNN fallback | Data tests in CI, review queue fed by workflows 5 and 6 |
| 4 | Automated blue/green reindex, hard-negative mining, drift job, embedder rollout by version | A full cycle from feedback to promoted embedder with a human approval only |
| 5 | 3-node cluster with replication, JWT roles, `user_memory`, optional `page_regions` | Failure drill passed (node loss, restore, rollback) |

## 17. Open questions

- Which embedding model and dimension will you use, and must it be multilingual (English only, or also Spanish and Portuguese)? This fixes the vector size, the storage numbers in section 10, and the intent and utterance data per language.
- How many documents, users, and tenants do you expect in the first year? That decides single node versus cluster, and shared versus dedicated collections.
- Self-hosted Qdrant on your own cluster, or managed Qdrant Cloud? Resharding and some operational features differ.
- Which Qdrant version will you pin? Memory-tier settings, `metadata`, and RRF parameters depend on it.
- May production utterances and feedback be stored and used for training, and for how long (retention)?
- Will templates be global only, or can tenants add their own (this decides the `scope` and `tenant_id` use in `templates`)?
- Is a learned sparse model worth adopting, or is BM25-style weighting enough for exact code names?
