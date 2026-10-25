"""Postman artifacts must be safe to commit and share: no secrets, no hardcoded hosts."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / "postman"
COLLECTION = ROOT / "voice-assistant.postman_collection.json"
ENVIRONMENTS = sorted((ROOT / "environments").glob("*.postman_environment.json"))
SECRET_KEYS = {"username", "password", "accessToken", "clientSecret", "lowPrivilegeToken"}
JWT = re.compile(r"eyJ[A-Za-z0-9_-]{10,}")


def test_collection_is_valid_postman_v2_1() -> None:
    data = json.loads(COLLECTION.read_text())
    assert (
        data["info"]["schema"]
        == "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    )
    assert data["info"]["name"] and data["item"]


def test_collection_has_no_tokens_or_credentials() -> None:
    text = COLLECTION.read_text()
    assert not JWT.search(text)
    data = json.loads(text)
    assert all(v["key"] not in SECRET_KEYS or v["value"] == "" for v in data.get("variable", []))


def test_every_request_targets_a_variable_host() -> None:
    def walk(items):  # type: ignore[no-untyped-def]
        for i in items:
            yield from walk(i["item"]) if "item" in i else [i]

    for item in walk(json.loads(COLLECTION.read_text())["item"]):
        assert item["request"]["url"]["raw"].startswith("{{"), item["name"]


def test_environments_exist_for_local_compose_and_staging() -> None:
    assert {p.name.split(".")[0] for p in ENVIRONMENTS} >= {"local", "docker-compose", "staging"}


@pytest.mark.parametrize("path", ENVIRONMENTS, ids=lambda p: p.name)
def test_environment_secrets_are_secret_typed_and_empty(path: Path) -> None:
    env = json.loads(path.read_text())
    values = {v["key"]: v for v in env["values"]}
    assert {"baseUrl", "keycloakUrl", "realm", "clientId", "authEnabled"} <= set(values)
    for key in SECRET_KEYS & set(values):
        assert values[key]["type"] == "secret" and values[key]["value"] == "", key
    assert not JWT.search(path.read_text())
    assert env["_postman_variable_scope"] == "environment"


def test_local_environment_points_at_localhost_only() -> None:
    env = json.loads((ROOT / "environments" / "local.postman_environment.json").read_text())
    base = next(v["value"] for v in env["values"] if v["key"] == "baseUrl")
    assert base.startswith("http://localhost")


def test_gitignore_blocks_local_secret_exports() -> None:
    text = (ROOT / ".gitignore").read_text()
    assert "*.local.postman_environment.json" in text and "*.secret.json" in text
