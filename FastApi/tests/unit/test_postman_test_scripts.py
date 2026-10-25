from pathlib import Path

import yaml
from scripts.postman_collection import build_collection, load_flows

ROOT = Path(__file__).resolve().parents[2]
OPENAPI = yaml.safe_load((ROOT / "api-contracts" / "openapi.yaml").read_text())
COLLECTION = build_collection(OPENAPI, load_flows(ROOT / "postman" / "flows"), ROOT / "postman")


def _script(item: dict) -> str:
    event = next(e for e in item["event"] if e["listen"] == "test")
    return "\n".join(event["script"]["exec"])


def _api_requests() -> list[dict]:
    return [
        i for f in COLLECTION["item"] if f["name"] != "Flows" for i in f["item"] if "request" in i
    ]


def test_collection_level_tests_check_correlation_id_latency_and_problem_shape() -> None:
    event = next(e for e in COLLECTION["event"] if e["listen"] == "test")
    text = "\n".join(event["script"]["exec"])
    assert "X-Correlation-ID" in text and "responseTime" in text
    assert "application/problem+json" in text and "'type'" in text and "'title'" in text


def test_every_request_asserts_status_content_type_and_schema() -> None:
    for item in _api_requests():
        text = _script(item)
        assert "pm.response.to.have.status(" in text or "to.include(pm.response.code)" in text, (
            item["name"]
        )
        assert "content-type" in text.lower(), item["name"]
        if "text/event-stream" not in text:  # streams have no JSON body to validate
            assert "jsonSchema" in text, item["name"]


def test_expected_status_is_the_documented_success_code() -> None:
    expected = {
        "/health/live": 200,
        "/health/ready": 200,
        "/v1/questions": 200,
        "/v1/ingestions": 202,
    }
    for item in _api_requests():
        raw = item["request"]["url"]["raw"].split("{{baseUrl}}")[1]
        if (
            raw in expected
            and item["request"]["method"] in {"GET", "POST"}
            and ":job_id" not in raw
        ):
            assert f"const expectedStatus = {expected[raw]};" in _script(item), raw


def test_flow_requests_carry_their_declared_expectations() -> None:
    flows = next(f for f in COLLECTION["item"] if f["name"] == "Flows")
    negative = next(f for f in flows["item"] if f["name"] == "Negative scenarios")
    unauth = next(i for i in negative["item"] if "401" in i["name"])
    assert "have.status(401)" in _script(unauth) or "expectedStatus = 401" in _script(unauth)
    assert "pm.test.skip" in _script(unauth)  # skipped when auth is disabled


def test_polling_flow_loops_until_the_job_finishes() -> None:
    flows = next(f for f in COLLECTION["item"] if f["name"] == "Flows")
    ingest = next(f for f in flows["item"] if f["name"] == "Ingest then ask")
    poll = next(i for i in ingest["item"] if "Poll" in i["name"])
    text = _script(poll)
    assert "postman.setNextRequest" in text and "succeeded" in text and "failed" in text
