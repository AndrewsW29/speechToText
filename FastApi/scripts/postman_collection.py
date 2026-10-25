"""OpenAPI 3.1 -> Postman Collection v2.1.

    uv run python scripts/postman_collection.py            # writes postman/voice-assistant.postman_collection.json
    uv run python scripts/postman_collection.py --check    # exits 1 when the committed file is stale

The collection has two parts: one folder per OpenAPI tag (a request per operation, with saved examples
and assertions, so it can never lack an endpoint) and a "Flows" folder merged from postman/flows/*.yaml
(happy paths, polling, negative scenarios).
"""

from __future__ import annotations

import copy
import json
import re
import sys
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
POSTMAN = ROOT / "postman"
OUTPUT = POSTMAN / "voice-assistant.postman_collection.json"
OPENAPI = ROOT / "api-contracts" / "openapi.yaml"
SCHEMA_URL = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
NAMESPACE = uuid.UUID("0b0a7c60-5c0e-4f4a-9f9e-5d3a3f1c2b11")
STATUS_TEXT = {
    200: "OK",
    202: "Accepted",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    413: "Payload Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    502: "Bad Gateway",
    503: "Service Unavailable",
}
FIXTURES = {"audio": "fixtures/question.webm", "file": "fixtures/sample.pdf"}
# Postman/Newman guess `video/webm` for .webm files; the API (like a browser MediaRecorder) uses audio/webm.
CONTENT_TYPES = {
    ".webm": "audio/webm",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
    ".mp4": "audio/mp4",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".txt": "text/plain",
}


def _file_field(key: str, src: str, content_type: str | None = None) -> dict[str, Any]:
    field: dict[str, Any] = {"key": key, "type": "file", "src": src}
    if kind := content_type or CONTENT_TYPES.get(Path(src).suffix):
        field["contentType"] = kind
    return field


FIELD_EXAMPLES = {
    "url": "{{ingestUrl}}",
    "language": "java",
    "framework": "spring",
    "job_id": "{{jobId}}",
}
PATH_VARIABLES = {"job_id": "{{jobId}}", "document_id": "{{documentId}}"}
# Values later requests of a folder need: stored right after the creating request succeeds.
CAPTURES = {
    ("post", "/v1/ingestions"): {"jobId": "job_id"},
    ("post", "/v1/documents"): {"documentId": "document_id"},
}
BODY_EXAMPLES: dict[tuple[str, str, int], Any] = {
    ("get", "/health/live", 200): {"status": "ok"},
    ("get", "/health/ready", 200): {"status": "ok", "checks": {}},
}
TAG_REQUIRES = {
    "ingestions": ["knowledge_base"],
    "documents": ["pdf_enabled"],
}  # these endpoints need Qdrant and the embedder
REQUIRES = {
    "auth": ("pm.variables.get('authEnabled') === 'false'", "auth is disabled"),
    "knowledge_base": (
        "pm.variables.get('knowledgeBase') !== 'true'",
        "the knowledge base is not configured",
    ),
    "small_audio_limit": (
        "pm.variables.get('smallAudioLimit') !== 'true'",
        "the API is not running with a small audio limit",
    ),
    "pdf_enabled": (
        "pm.variables.get('pdfEnabled') !== 'true'",
        "PDF ingestion is not enabled on this API",
    ),
    "low_privilege_token": (
        "!pm.variables.get('lowPrivilegeToken')",
        "no lowPrivilegeToken is set",
    ),
}


def _uid(*parts: str) -> str:
    return str(uuid.uuid5(NAMESPACE, "/".join(parts)))


# ------------------------------------------------------------------ schema helpers
def resolve(
    schema: Mapping[str, Any], spec: Mapping[str, Any], seen: tuple[str, ...] = ()
) -> dict[str, Any]:
    """Inline $refs (cycle-safe) so the result is a self-contained JSON Schema."""
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref in seen:
            return {}
        target: Any = spec
        for part in ref.removeprefix("#/").split("/"):
            target = target[part]
        return resolve(target, spec, (*seen, ref))
    out: dict[str, Any] = {}
    for key, value in schema.items():
        if key == "properties":
            out[key] = {k: resolve(v, spec, seen) for k, v in value.items()}
        elif key in {"items", "additionalProperties"} and isinstance(value, dict):
            out[key] = resolve(value, spec, seen)
        elif key in {"anyOf", "oneOf", "allOf"}:
            out[key] = [resolve(v, spec, seen) for v in value]
        else:
            out[key] = value
    return out


def example(schema: Mapping[str, Any], name: str = "") -> Any:
    """A representative value for a resolved schema."""
    if (name in FIELD_EXAMPLES and schema.get("type") in {"string", None}) or (
        name in FIELD_EXAMPLES and "anyOf" in schema
    ):
        return FIELD_EXAMPLES[name]
    if "example" in schema:
        return schema["example"]
    if "default" in schema and schema["default"] is not None:
        return schema["default"]
    for key in ("anyOf", "oneOf"):
        if key in schema:
            options = [o for o in schema[key] if o.get("type") != "null"]
            return example(options[0], name) if options else None
    if "allOf" in schema:
        return example(schema["allOf"][0], name)
    kind = schema.get("type")
    if kind == "object" or "properties" in schema:
        props = schema.get("properties", {})
        if not props and isinstance(schema.get("additionalProperties"), dict):
            return {"key": example(schema["additionalProperties"])}
        return {k: example(v, k) for k, v in props.items()}
    if kind == "array":
        return [example(schema.get("items", {}))]
    if kind == "integer":
        return 0
    if kind == "number":
        return 0.0
    if kind == "boolean":
        return True
    return schema.get("enum", ["string"])[0] if kind == "string" or kind is None else None


# ------------------------------------------------------------------ script builders
def _js(lines: list[str]) -> dict[str, Any]:
    return {"type": "text/javascript", "exec": lines}


def _event(listen: str, lines: list[str]) -> dict[str, Any]:
    return {"listen": listen, "script": _js(lines)}


def test_lines(
    expected: int,
    content_type: str | None,
    schema: dict[str, Any] | None,
    accepted: list[int] | None = None,
) -> list[str]:
    lines = [f"const expectedStatus = {expected};"]
    if accepted and len(accepted) > 1:  # e.g. 202 for a new upload, 200 for a duplicate
        lines += [
            f"const acceptedStatuses = {json.dumps(accepted)};",
            "pm.test(`status is one of ${acceptedStatuses}`, () => "
            "pm.expect(acceptedStatuses).to.include(pm.response.code));",
        ]
    else:
        lines.append(
            "pm.test(`status is ${expectedStatus}`, () => pm.response.to.have.status(expectedStatus));"
        )
    if content_type:
        lines.append(
            f"pm.test('content-type is {content_type}', () => "
            f"pm.expect(pm.response.headers.get('Content-Type')).to.include('{content_type}'));"
        )
    if schema is not None and content_type == "application/json":
        lines.append(f"const schema = {json.dumps(schema, sort_keys=True)};")
        lines.append(
            "pm.test('response matches the OpenAPI schema', () => pm.response.to.have.jsonSchema(schema));"
        )
    return lines


def _guard(requires: list[str], body: list[str]) -> list[str]:
    """Wrap assertions so the request still runs but reports a skipped test when a precondition is off."""
    if not requires:
        return body
    cond = " || ".join(REQUIRES[r][0] for r in requires)
    reason = " and ".join(REQUIRES[r][1] for r in requires)
    return [
        f"if ({cond}) {{",
        f"  pm.test.skip('skipped: {reason}');",
        "} else {",
        *["  " + line for line in body],
        "}",
    ]


# ------------------------------------------------------------------ auto-generated tag folders
def _url(path: str, variables: list[dict[str, str]] | None = None) -> dict[str, Any]:
    segments = [s for s in path.split("/") if s]
    url: dict[str, Any] = {"raw": "{{baseUrl}}" + path, "host": ["{{baseUrl}}"], "path": segments}
    if variables:
        url["variable"] = variables
    return url


def _request_body(op: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any] | None:
    content = op.get("requestBody", {}).get("content", {})
    if "multipart/form-data" in content:
        schema = resolve(content["multipart/form-data"]["schema"], spec)
        fields = []
        for name, prop in schema.get("properties", {}).items():
            if prop.get("format") == "binary" or name in FIXTURES:
                fields.append(_file_field(name, FIXTURES.get(name, "fixtures/question.webm")))
            else:
                fields.append(
                    {
                        "key": name,
                        "type": "text",
                        "value": str(example(prop, name)),
                        "disabled": True,
                    }
                )
        return {"mode": "formdata", "formdata": fields}
    if "application/json" in content:
        schema = resolve(content["application/json"]["schema"], spec)
        return {
            "mode": "raw",
            "raw": json.dumps(example(schema), indent=2),
            "options": {"raw": {"language": "json"}},
        }
    return None


def _saved_responses(
    method: str, path: str, op: Mapping[str, Any], spec: Mapping[str, Any], request: dict[str, Any]
) -> list[dict[str, Any]]:
    saved = []
    for code_text, response in op["responses"].items():
        code = int(code_text)
        content = response.get("content", {})
        content_type = next(iter(content), "application/json")
        if code >= 400:
            body: Any = {"type": "about:blank", "title": response["description"], "status": code}
        elif (method, path, code) in BODY_EXAMPLES:
            body = BODY_EXAMPLES[(method, path, code)]
        else:
            body = example(resolve(content.get(content_type, {}).get("schema", {}), spec))
        saved.append(
            {
                "name": f"{code} {response['description']}",
                "originalRequest": {"method": request["method"], "url": request["url"]},
                "status": STATUS_TEXT.get(code, "Response"),
                "code": code,
                "_postman_previewlanguage": "json",
                "header": [{"key": "Content-Type", "value": content_type}],
                "body": json.dumps(body, indent=2),
            }
        )
    return saved


def _operation_item(
    method: str, path: str, op: Mapping[str, Any], spec: Mapping[str, Any]
) -> dict[str, Any]:
    names = re.findall(r"{(\w+)}", path)
    postman_path = re.sub(r"{(\w+)}", r":\1", path)
    variables = [{"key": n, "value": PATH_VARIABLES.get(n, "{{" + n + "}}")} for n in names] or None
    request: dict[str, Any] = {
        "method": method.upper(),
        "header": [{"key": "Accept", "value": "application/json"}],
        "url": _url(postman_path, variables),
        "description": op.get("description") or op.get("summary", ""),
    }
    if not op.get("security"):
        request["auth"] = {"type": "noauth"}
    if body := _request_body(op, spec):
        request["body"] = body
    successes = [int(c) for c in op["responses"] if str(c).startswith("2")]
    success = successes[0]
    ok = (
        op["responses"][str(success)]
        if str(success) in op["responses"]
        else op["responses"][success]
    )
    content = ok.get("content", {})
    content_type = (
        "text/event-stream" if "text/event-stream" in content else next(iter(content), None)
    )
    schema = resolve(content[content_type]["schema"], spec) if content_type else None
    lines = test_lines(success, content_type, schema, successes)
    if captures := CAPTURES.get((method, path)):
        lines.append("const payload = pm.response.json();")
        lines += [
            f"if (payload.{field} !== undefined) pm.collectionVariables.set('{var}', payload.{field});"
            for var, field in captures.items()
        ]
    required = [r for t in op.get("tags", []) for r in TAG_REQUIRES.get(t, [])]
    return {
        "name": f"{method.upper()} {path}",
        "event": [_event("test", _guard(required, lines))],
        "request": request,
        "response": _saved_responses(method, path, op, spec, request),
    }


def _tag_folders(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    folders: dict[str, list[dict[str, Any]]] = {}
    for path, item in spec["paths"].items():
        for method, op in item.items():
            for tag in op.get("tags", ["default"]):
                folders.setdefault(tag, []).append(_operation_item(method, path, op, spec))
    return [{"name": tag, "item": items} for tag, items in sorted(folders.items())]


# ------------------------------------------------------------------ hand-authored flows
def load_flows(directory: Path) -> list[dict[str, Any]]:
    flows = [
        yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.yaml"))
    ]
    return sorted(flows, key=lambda f: (f.get("order", 99), f["name"]))


def _flow_body(body: Mapping[str, Any]) -> dict[str, Any]:
    if body["type"] == "formdata":
        fields = []
        for f in body["fields"]:
            field = (
                _file_field(f["key"], f["src"], f.get("content_type"))
                if f["type"] == "file"
                else {"key": f["key"], "type": "text", "value": f.get("value")}
            )
            if f.get("disabled"):
                field["disabled"] = True
            fields.append(field)
        return {"mode": "formdata", "formdata": fields}
    return {
        "mode": "raw",
        "raw": json.dumps(body["value"], indent=2),
        "options": {"raw": {"language": "json"}},
    }


def _flow_assertions(req: Mapping[str, Any]) -> list[str]:
    expect = req.get("expect", {})
    lines = test_lines(expect["status"], expect.get("content_type"), None)
    if req.get("capture"):
        lines.append("const payload = pm.response.json();")
        for var, path in req["capture"].items():
            lines.append(
                f"if (payload.{path} !== undefined) pm.collectionVariables.set('{var}', payload.{path});"
            )
    for key, value in (expect.get("json") or {}).items():
        lines.append(
            f"pm.test('{key} is {value}', () => pm.expect(pm.response.json().{key}).to.equal({json.dumps(value)}));"
        )
    for check in expect.get("checks", []):
        accessor = "pm.response.json()." + check["path"]
        if check.get("nonempty"):
            lines.append(
                f"pm.test('{check['path']} is not empty', () => pm.expect({accessor}).to.be.a('string').that.is.not.empty);"
            )
        if "in" in check:
            options = ", ".join(check["in"])
            lines.append(
                f"pm.test('{check['path']} is one of {options}', () => pm.expect({json.dumps(check['in'])}).to.include({accessor}));"
            )
    lines.extend(expect.get("script", []))
    if poll := req.get("poll"):
        lines.extend(_poll_lines(poll))
    return lines


def _poll_lines(poll: Mapping[str, Any]) -> list[str]:
    return [
        "const state = pm.response.json().state;",
        f"const pending = {json.dumps(poll['states_pending'])};",
        f"const terminal = {json.dumps(poll['terminal'])};",
        "const attempt = Number(pm.collectionVariables.get('pollAttempt') || 0) + 1;",
        f"if (pending.includes(state) && attempt < {poll['max_attempts']}) {{",
        "  pm.collectionVariables.set('pollAttempt', String(attempt));",
        "  postman.setNextRequest(pm.info.requestName);",
        "} else {",
        "  pm.collectionVariables.unset('pollAttempt');",
        "  pm.test(`job reached a terminal state (${state})`, () => pm.expect(terminal).to.include(state));",
        "  pm.test('job succeeded', () => pm.expect(state).to.equal('succeeded'));",
        "}",
    ]


def _flow_request(req: Mapping[str, Any]) -> dict[str, Any]:
    path = req["path"]
    variables = [{"key": k, "value": v} for k, v in req.get("path_vars", {}).items()] or None
    request: dict[str, Any] = {
        "method": req["method"],
        "header": [
            {"key": "Accept", "value": "application/json"},
            *({"key": k, "value": v} for k, v in req.get("headers", {}).items()),
        ],
        "url": _url(path, variables),
    }
    if req.get("auth") == "noauth":
        request["auth"] = {"type": "noauth"}
    if "body" in req:
        request["body"] = _flow_body(req["body"])
    events = [_event("test", _guard(req.get("requires", []), _flow_assertions(req)))]
    if delay := req.get("poll", {}).get("delay_ms"):
        events.insert(
            0,
            _event(
                "prerequest",
                [f"const until = Date.now() + {delay};", "while (Date.now() < until) {}"],
            ),
        )
    return {"name": req["name"], "event": events, "request": request}


def _flows_folder(flows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "name": "Flows",
        "description": "Hand-authored scenarios. Run a folder with the Collection Runner or Newman.",
        "item": [
            {
                "name": f["name"],
                "description": f.get("description", ""),
                "item": [_flow_request(r) for r in f["requests"]],
            }
            for f in flows
        ],
    }


# ------------------------------------------------------------------ assembly
def build_collection(
    spec: Mapping[str, Any], flows: list[dict[str, Any]], postman_dir: Path
) -> dict[str, Any]:
    pre = (postman_dir / "scripts" / "pre-request.js").read_text(encoding="utf-8").splitlines()
    tests = (postman_dir / "scripts" / "tests.js").read_text(encoding="utf-8").splitlines()
    info = spec["info"]
    return {
        "info": {
            "_postman_id": _uid("collection", info["title"]),
            "name": f"{info['title']} (v{info['version']})",
            "description": "Generated from api-contracts/openapi.yaml by scripts/postman_collection.py. "
            "Do not edit by hand: change the contract or postman/flows/*.yaml and run `make postman`.",
            "schema": SCHEMA_URL,
        },
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{accessToken}}", "type": "string"}],
        },
        "event": [_event("prerequest", pre), _event("test", tests)],
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8000"},
            {"key": "jobId", "value": ""},
            {"key": "questionId", "value": ""},
            {"key": "pollAttempt", "value": ""},
        ],
        "item": [*copy.deepcopy(_tag_folders(spec)), _flows_folder(flows)],
    }


def render(collection: Mapping[str, Any]) -> str:
    return json.dumps(collection, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    spec = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    text = render(build_collection(spec, load_flows(POSTMAN / "flows"), POSTMAN))
    if "--check" in argv:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != text:
            print("collection is stale: run `make postman`", file=sys.stderr)
            return 1
        return 0
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
