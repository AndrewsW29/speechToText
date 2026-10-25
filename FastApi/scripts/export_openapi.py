"""Export the OpenAPI contract: `uv run python scripts/export_openapi.py > api-contracts/openapi.yaml`."""

import sys

import yaml
from app.config import Settings
from app.container import Container
from app.main import create_app

PROBLEM = {
    "type": "object",
    "required": ["type", "title", "status"],
    "properties": {
        "type": {"type": "string", "default": "about:blank"},
        "title": {"type": "string"},
        "status": {"type": "integer"},
        "detail": {"type": "string"},
        "fields": {"type": "array", "items": {"type": "string"}},
    },
}


def build() -> dict:  # type: ignore[type-arg]
    app = create_app(Settings(auth_enabled=False), container=Container(ask_question=None))  # type: ignore[arg-type]
    spec = app.openapi()
    spec["openapi"] = "3.1.0"
    spec["components"].setdefault("schemas", {})["ProblemDetails"] = PROBLEM
    spec["components"]["securitySchemes"] = {
        "bearer": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    ref = {
        "content": {
            "application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}
        }
    }

    def add_errors(op: dict, errors: dict[str, str]) -> None:  # type: ignore[type-arg]
        op["security"] = [{"bearer": []}]
        op["responses"].pop("422", None)
        for code, desc in errors.items():
            op["responses"][code] = {"description": desc, **ref}

    add_errors(
        spec["paths"]["/v1/questions"]["post"],
        {
            "401": "Missing or invalid token",
            "404": "No relevant knowledge found",
            "413": "Audio too large",
            "415": "Unsupported media type",
            "422": "Invalid audio or validation failure",
            "502": "Speech-to-text unavailable",
        },
    )
    ingest_errors = {
        "401": "Missing or invalid token",
        "403": "Requires the 'ingest' role",
        "404": "Ingestion job not found",
        "422": "Validation failed or URL not allowed",
        "503": "Ingestion is not configured",
    }
    add_errors(spec["paths"]["/v1/ingestions"]["post"], ingest_errors)
    add_errors(spec["paths"]["/v1/ingestions/{job_id}"]["get"], ingest_errors)
    return spec


if __name__ == "__main__":
    yaml.safe_dump(build(), sys.stdout, sort_keys=False)
