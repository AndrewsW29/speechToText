"""Publish the collection and environments to a Postman workspace (manual use / workflow_dispatch).

    POSTMAN_API_KEY=... POSTMAN_WORKSPACE_ID=... uv run python scripts/postman_sync.py

Existing items are matched by name and updated in place; secret-typed values are never uploaded.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

POSTMAN = Path(__file__).resolve().parents[1] / "postman"
API = "https://api.getpostman.com"


class PostmanSyncError(RuntimeError):
    pass


def _call(client: httpx.Client, key: str, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    try:
        response = client.request(method, path, headers={"X-API-Key": key}, **kwargs)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        status = getattr(getattr(exc, "response", None), "status_code", "network error")
        raise PostmanSyncError(f"Postman API {method} {path} failed ({status})") from None
    return dict(response.json())


def _public(env: dict[str, Any]) -> dict[str, Any]:
    clean = dict(env)
    clean["values"] = [v for v in env.get("values", []) if v.get("type") != "secret"]
    return clean


def sync(
    client: httpx.Client,
    key: str,
    workspace: str,
    collection: dict[str, Any],
    environments: list[dict[str, Any]],
) -> dict[str, Any]:
    if not key:
        raise PostmanSyncError("POSTMAN_API_KEY is not set")
    if not workspace:
        raise PostmanSyncError("POSTMAN_WORKSPACE_ID is not set")
    params = {"workspace": workspace}

    name = collection["info"]["name"]
    found = {
        c["name"]: c["uid"]
        for c in _call(client, key, "GET", "/collections", params=params)["collections"]
    }
    if name in found:
        _call(client, key, "PUT", f"/collections/{found[name]}", json={"collection": collection})
        result: dict[str, Any] = {"collection": "updated", "environments": {}}
    else:
        _call(client, key, "POST", "/collections", params=params, json={"collection": collection})
        result = {"collection": "created", "environments": {}}

    existing = {
        e["name"]: e["uid"]
        for e in _call(client, key, "GET", "/environments", params=params)["environments"]
    }
    for env in environments:
        body = {"environment": _public(env)}
        if env["name"] in existing:
            _call(client, key, "PUT", f"/environments/{existing[env['name']]}", json=body)
            result["environments"][env["name"]] = "updated"
        else:
            _call(client, key, "POST", "/environments", params=params, json=body)
            result["environments"][env["name"]] = "created"
    return result


def main() -> int:
    collection = json.loads((POSTMAN / "voice-assistant.postman_collection.json").read_text())
    environments = [
        json.loads(p.read_text()) for p in sorted((POSTMAN / "environments").glob("*.json"))
    ]
    try:
        with httpx.Client(base_url=API, timeout=30) as client:
            print(
                json.dumps(
                    sync(
                        client,
                        os.environ.get("POSTMAN_API_KEY", ""),
                        os.environ.get("POSTMAN_WORKSPACE_ID", ""),
                        collection,
                        environments,
                    ),
                    indent=2,
                )
            )
    except PostmanSyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
