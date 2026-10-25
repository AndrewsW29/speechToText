"""The committed collection is generated from openapi.yaml and must not drift from it."""

import json
import re
from pathlib import Path

import yaml
from scripts.postman_collection import build_collection, load_flows, render

ROOT = Path(__file__).resolve().parents[2]
COLLECTION = ROOT / "postman" / "voice-assistant.postman_collection.json"
OPENAPI = yaml.safe_load((ROOT / "api-contracts" / "openapi.yaml").read_text())


def test_committed_collection_is_in_sync_with_the_contract_and_flows() -> None:
    fresh = render(
        build_collection(OPENAPI, load_flows(ROOT / "postman" / "flows"), ROOT / "postman")
    )
    assert COLLECTION.read_text() == fresh, "run `make postman` and commit the result"


def test_every_openapi_operation_is_in_the_committed_collection() -> None:
    committed = json.loads(COLLECTION.read_text())
    present = {
        (i["request"]["method"], i["request"]["url"]["raw"].split("{{baseUrl}}")[1])
        for f in committed["item"]
        if f["name"] != "Flows"
        for i in f["item"]
        if "request" in i
    }
    for path, item in OPENAPI["paths"].items():
        for method in item:
            assert (method.upper(), re.sub(r"{(\w+)}", r":\1", path)) in present, f"{method} {path}"


def test_flow_folders_exist_in_a_sensible_order() -> None:
    committed = json.loads(COLLECTION.read_text())
    flows = next(f for f in committed["item"] if f["name"] == "Flows")
    names = [f["name"] for f in flows["item"]]
    assert names[:4] == ["Health", "Ask a question", "Ingest then ask", "Negative scenarios"]


def test_every_flow_fixture_file_exists() -> None:
    committed = json.loads(COLLECTION.read_text())

    def walk(items):  # type: ignore[no-untyped-def]
        for i in items:
            yield from walk(i["item"]) if "item" in i else [i]

    for request in walk(committed["item"]):
        for field in request["request"].get("body", {}).get("formdata", []):
            if field["type"] == "file":
                assert (ROOT / "postman" / field["src"]).exists(), field["src"]
