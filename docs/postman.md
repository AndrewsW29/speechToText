# Postman collections

The collection is **generated** from `FastApi/api-contracts/openapi.yaml` plus the hand-written scenarios in
`FastApi/postman/flows/*.yaml`. Never edit `voice-assistant.postman_collection.json` by hand: change the contract
or a flow, then run `make postman` (from `FastApi/`). CI and a pre-commit hook fail when the file is stale.

## What is in it

| Folder | Content |
| :--- | :--- |
| `health`, `questions`, `ingestions` | One request per OpenAPI operation, with saved examples for every documented status (including `application/problem+json`) and assertions for status, content type and response schema |
| `Flows / Health` | Liveness and readiness |
| `Flows / Ask a question` | Upload audio, check the transcript and that every answer cites a source |
| `Flows / Ingest then ask` | Submit an ingestion job, poll it to a terminal state, then ask a grounded question (needs the knowledge base) |
| `Flows / Negative scenarios` | 401, 403, 404, 413, 415 (two kinds), 422 (two kinds) |

Collection-level scripts add an `X-Correlation-ID` to every request, fetch a Keycloak token when auth is on, and assert
the correlation id, the latency budget (`latencyBudgetMs`, default 5000) and the RFC 9457 problem shape for every error.

## Use it in Postman

1. Import `FastApi/postman/voice-assistant.postman_collection.json` and one file from `FastApi/postman/environments/`.
2. Select the environment. Set `baseUrl` if needed.
3. Authentication (skip when `authEnabled=false`): either paste a token into `accessToken`, or fill `username` and
   `password` (the pre-request script gets and refreshes a token from Keycloak), or set `clientSecret` for client credentials.
   Secret-typed values stay on your machine: do not export them. `*.local.postman_environment.json` is git-ignored.
4. Run a folder, or open a request and press **Send**.

Local stack: `docker compose -f FastApi/deploy/docker/docker-compose.yml up` (copy `.env.example` to `.env` first).
Users `dev-user` (no role) and `dev-ingester` (role `ingest`) get their passwords from `DEV_USER_PASSWORD` and
`DEV_INGESTER_PASSWORD`. For the 403 scenario, put a `dev-user` token in `lowPrivilegeToken`.

## Run it from the command line

```bash
make newman ENV=docker-compose            # needs Node; or: make newman-docker (uses the official image)
make newman-docker ENV=local BASE_URL=http://localhost:8000
```

To exercise everything without real audio or auth, start the API with the fake STT engine:

```bash
VA_AUTH_ENABLED=false VA_STT_ENGINE=fake VA_MAX_AUDIO_BYTES=2048 uv run uvicorn app.main:create_app --factory
make newman-docker ENV=local   # add --env-var smallAudioLimit=true authEnabled=false via the flags in postman.yml
```

Scenarios that need something that is off are reported as **skipped**, not failed: `authEnabled=false` skips 401/403,
`knowledgeBase=false` skips ingestion, `smallAudioLimit=false` skips the 413 check.

`VA_STT_ENGINE=fake` returns a fixed transcript for any non-empty audio and **refuses to start when
`VA_ENVIRONMENT=production`**. Against Whisper use `postman/fixtures/question.real.webm` (`make fixtures` records one
on macOS with `say` and `ffmpeg`).

## Add or change an endpoint

1. Update the API and regenerate the contract (`uv run python scripts/export_openapi.py > api-contracts/openapi.yaml`).
2. `make postman`: the new operation appears automatically with assertions and examples.
3. For a scenario, add a request to a file in `postman/flows/` (see `negative.yaml` for every supported key:
   `body`, `expect`, `capture`, `poll`, `requires`, `headers`, `path_vars`, `script`).
4. Commit the regenerated collection. `make postman-check` verifies it.

## Mock server for client developers

`make mock-api` starts Prism on `http://localhost:4010`, answering from the OpenAPI examples. Point the Angular, Android
and iOS clients at it to build screens before the backend exists.

## Publish to a Postman workspace (optional)

Run the `postman` workflow manually with **publish** ticked. It needs the repository secrets `POSTMAN_API_KEY` and
`POSTMAN_WORKSPACE_ID`, matches collections and environments by name, and never uploads secret-typed values.
Locally: `POSTMAN_API_KEY=... POSTMAN_WORKSPACE_ID=... uv run python scripts/postman_sync.py`.

## Security

No token, password or hostname lives in the collection or in the committed environments (tests enforce it). The
`voice-postman` Keycloak client allows the password grant for development only; do not import that realm into production.
