import json
import re
from pathlib import Path

import pytest
import yaml
from scripts.postman_collection import build_collection, load_flows

ROOT = Path(__file__).resolve().parents[2]
OPENAPI = yaml.safe_load((ROOT / "api-contracts" / "openapi.yaml").read_text())
COLLECTION = build_collection(OPENAPI, load_flows(ROOT / "postman" / "flows"), ROOT / "postman")
TAG_FOLDERS = {f["name"]: f for f in COLLECTION["item"] if f["name"] != "Flows"}
OPS = [(m.upper(), p, op) for p, item in OPENAPI["paths"].items() for m, op in item.items()]


def _requests(folder: dict) -> list[dict]:
    return [i for i in folder["item"] if "request" in i]


def test_one_folder_per_openapi_tag_and_one_request_per_operation() -> None:
    tags = {t for _, _, op in OPS for t in op.get("tags", [])}
    assert set(TAG_FOLDERS) == tags
    assert sum(len(_requests(f)) for f in TAG_FOLDERS.values()) == len(OPS)


def test_requests_use_the_base_url_variable_and_never_a_hardcoded_host() -> None:
    for folder in TAG_FOLDERS.values():
        for item in _requests(folder):
            url = item["request"]["url"]
            assert url["raw"].startswith("{{baseUrl}}/") and url["host"] == ["{{baseUrl}}"]


def test_collection_level_bearer_auth_uses_the_access_token_variable() -> None:
    bearer = COLLECTION["auth"]
    assert bearer["type"] == "bearer" and bearer["bearer"][0]["value"] == "{{accessToken}}"


def test_public_operations_opt_out_of_auth_and_secured_ones_inherit_it() -> None:
    by_name = {
        (i["request"]["method"], i["request"]["url"]["raw"].split("{{baseUrl}}")[1]): i
        for f in TAG_FOLDERS.values()
        for i in _requests(f)
    }
    for method, path, op in OPS:
        item = by_name[(method, re.sub(r"{(\w+)}", r":\1", path))]
        auth = item["request"].get("auth", {})
        if op.get("security"):
            assert auth.get("type") != "noauth", (method, path)
        else:
            assert auth == {"type": "noauth"}, (method, path)


def test_audio_upload_is_a_multipart_file_field() -> None:
    ask = next(i for i in _requests(TAG_FOLDERS["questions"]) if i["request"]["method"] == "POST")
    body = ask["request"]["body"]
    assert body["mode"] == "formdata"
    audio = next(f for f in body["formdata"] if f["key"] == "audio")
    assert audio["type"] == "file" and audio["src"].endswith(".webm")


def test_json_bodies_use_schema_examples_and_path_params_use_variables() -> None:
    submit = next(
        i for i in _requests(TAG_FOLDERS["ingestions"]) if i["request"]["method"] == "POST"
    )
    payload = json.loads(submit["request"]["body"]["raw"])
    assert set(payload) >= {"url"} and payload["url"].startswith("{{")
    status = next(
        i for i in _requests(TAG_FOLDERS["ingestions"]) if i["request"]["method"] == "GET"
    )
    assert status["request"]["url"]["variable"] == [{"key": "job_id", "value": "{{jobId}}"}]


@pytest.mark.parametrize(("method", "path", "op"), OPS, ids=[f"{m} {p}" for m, p, _ in OPS])
def test_every_documented_response_has_a_saved_example(method: str, path: str, op: dict) -> None:
    item = next(
        i
        for f in TAG_FOLDERS.values()
        for i in _requests(f)
        if i["request"]["method"] == method
        and i["request"]["url"]["raw"].endswith(re.sub(r"{(\w+)}", r":\1", path))
    )
    saved = {r["code"]: r for r in item["response"]}
    assert set(saved) == {int(c) for c in op["responses"]}
    for code, example in saved.items():
        content_type = next(h["value"] for h in example["header"] if h["key"] == "Content-Type")
        body = json.loads(example["body"])
        if code >= 400:
            assert content_type == "application/problem+json"
            assert body["status"] == code and {"type", "title", "status"} <= set(body)


def test_collection_script_acquires_a_keycloak_token() -> None:
    pre = next(e for e in COLLECTION["event"] if e["listen"] == "prerequest")
    text = "\n".join(pre["script"]["exec"])
    assert "grant_type" in text and "X-Correlation-ID" in text and "accessToken" in text


def test_generation_is_deterministic() -> None:
    again = build_collection(OPENAPI, load_flows(ROOT / "postman" / "flows"), ROOT / "postman")
    assert json.dumps(again) == json.dumps(COLLECTION)
