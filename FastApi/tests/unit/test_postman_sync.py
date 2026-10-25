import json

import httpx
import pytest
from scripts.postman_sync import PostmanSyncError, sync

COLLECTION = {"info": {"name": "Voice Assistant API (v0.1.0)", "schema": "x"}, "item": []}
ENV = {"name": "Voice Assistant: local", "values": []}


def _client(existing_collections=None, existing_envs=None, seen=None):  # type: ignore[no-untyped-def]
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append((request.method, request.url.path, request.headers.get("x-api-key")))
        path = request.url.path
        if request.method == "GET" and path == "/collections":
            return httpx.Response(200, json={"collections": existing_collections or []})
        if request.method == "GET" and path == "/environments":
            return httpx.Response(200, json={"environments": existing_envs or []})
        return httpx.Response(200, json={"collection": {"uid": "u1"}, "environment": {"uid": "e1"}})

    return httpx.Client(
        base_url="https://api.getpostman.com", transport=httpx.MockTransport(handler)
    )


def test_creates_the_collection_and_environments_when_absent() -> None:
    seen: list = []
    result = sync(_client(seen=seen), "key", "ws1", COLLECTION, [ENV])
    assert result == {
        "collection": "created",
        "environments": {"Voice Assistant: local": "created"},
    }
    assert ("POST", "/collections", "key") in seen and ("POST", "/environments", "key") in seen


def test_updates_in_place_when_the_name_already_exists() -> None:
    seen: list = []
    client = _client(
        [{"uid": "c9", "name": COLLECTION["info"]["name"]}],
        [{"uid": "e9", "name": ENV["name"]}],
        seen,
    )
    result = sync(client, "key", "ws1", COLLECTION, [ENV])
    assert result["collection"] == "updated"
    assert ("PUT", "/collections/c9", "key") in seen and ("PUT", "/environments/e9", "key") in seen


def test_secret_values_are_never_sent() -> None:
    sent: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method in {"POST", "PUT"}:
            sent.append(json.loads(request.content))
        return httpx.Response(
            200, json={"collections": [], "environments": [], "collection": {}, "environment": {}}
        )

    env = {
        "name": "e",
        "values": [
            {"key": "password", "value": "hunter2", "type": "secret"},
            {"key": "baseUrl", "value": "http://x", "type": "default"},
        ],
    }
    client = httpx.Client(
        base_url="https://api.getpostman.com", transport=httpx.MockTransport(handler)
    )
    sync(client, "key", "ws1", COLLECTION, [env])
    assert "hunter2" not in json.dumps(sent)


def test_missing_credentials_and_api_errors_are_reported_without_leaking_the_key() -> None:
    with pytest.raises(PostmanSyncError, match="POSTMAN_API_KEY"):
        sync(_client(), "", "ws1", COLLECTION, [])
    failing = httpx.Client(
        base_url="https://api.getpostman.com",
        transport=httpx.MockTransport(lambda r: httpx.Response(401, json={"error": "bad"})),
    )
    with pytest.raises(PostmanSyncError) as err:
        sync(failing, "super-secret-key", "ws1", COLLECTION, [ENV])
    assert "super-secret-key" not in str(err.value)
