"""The committed OpenAPI file is the single source of truth for generated clients."""

from pathlib import Path

import yaml
from scripts.export_openapi import build

CONTRACT = Path(__file__).resolve().parents[2] / "api-contracts" / "openapi.yaml"


def test_committed_contract_matches_the_app() -> None:
    assert yaml.safe_load(CONTRACT.read_text()) == yaml.safe_load(yaml.safe_dump(build()))


def test_contract_declares_problem_details_for_errors() -> None:
    post = yaml.safe_load(CONTRACT.read_text())["paths"]["/v1/questions"]["post"]
    for code in ("401", "404", "413", "415", "422", "502"):
        assert "application/problem+json" in post["responses"][code]["content"]


def test_ingestion_endpoints_are_secured_and_documented() -> None:
    paths = yaml.safe_load(CONTRACT.read_text())["paths"]
    assert "202" in paths["/v1/ingestions"]["post"]["responses"]
    for op in (paths["/v1/ingestions"]["post"], paths["/v1/ingestions/{job_id}"]["get"]):
        assert op["security"] == [{"bearer": []}]
        assert "403" in op["responses"]
