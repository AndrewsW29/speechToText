"""tusd HTTP hooks: validate on pre-create, ingest on post-finish. Internal, tusd only."""

from __future__ import annotations

import hmac
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.adapters.inbound.rest.auth import ANONYMOUS, JwtVerifier, Principal
from app.adapters.inbound.rest.errors import ProblemError
from app.application.errors import (
    NotAPdfError,
    QuotaExceededError,
    TooLargeError,
    UploadRejectedError,
)
from app.application.pdf.services.validation import PdfLimits
from app.config import Settings

router = APIRouter(prefix="/internal/tus", include_in_schema=False)
UPLOAD_ID = re.compile(r"^[A-Za-z0-9]{1,128}$")


def _reject(status: int, message: str) -> dict[str, Any]:
    return {"RejectUpload": True, "HTTPResponse": {"StatusCode": status, "Body": message}}


def _principal(request: Request, payload: dict[str, Any]) -> Principal | None:
    settings: Settings = request.app.state.settings
    if not settings.auth_enabled:
        return ANONYMOUS
    headers = payload.get("Event", {}).get("HTTPRequest", {}).get("Header", {})
    raw = (headers.get("Authorization") or headers.get("authorization") or [""])[0]
    scheme, _, token = raw.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    verifier: JwtVerifier = request.app.state.verifier
    try:
        return verifier.verify(token)
    except ProblemError:
        return None


def _discard(directory: Path, upload_id: str) -> None:
    for suffix in ("", ".info", ".lock"):
        (directory / f"{upload_id}{suffix}").unlink(missing_ok=True)


@router.post("/hooks/{token}")
async def hook(token: str, request: Request, payload: dict[str, Any] = Body(...)) -> JSONResponse:  # noqa: B008
    settings: Settings = request.app.state.settings
    expected = settings.tus_hook_token.get_secret_value() if settings.tus_hook_token else None
    if not expected or not hmac.compare_digest(token, expected):
        raise ProblemError(404, "Not found")

    kind = payload.get("Type")
    upload = payload.get("Event", {}).get("Upload", {})
    principal = _principal(request, payload)

    if kind == "pre-create":
        if principal is None:
            return JSONResponse(_reject(401, "Missing or invalid token"))
        if int(upload.get("Size") or 0) > PdfLimits.from_settings(settings).max_file_bytes:
            return JSONResponse(_reject(413, "The file is too large"))
        return JSONResponse({})

    if kind != "post-finish":
        return JSONResponse({})

    upload_id = str(upload.get("ID", ""))
    if not UPLOAD_ID.match(upload_id) or settings.tus_upload_dir is None:
        raise ProblemError(422, "Invalid upload id")
    directory = settings.tus_upload_dir
    path = directory / upload_id
    try:
        if principal is None:
            return JSONResponse({"rejected": "unauthorized"})
        use_case = request.app.state.container.upload_document
        if use_case is None or not path.is_file():
            raise ProblemError(503, "Document processing is not configured")
        filename = (upload.get("MetaData") or {}).get("filename")
        data = await run_in_threadpool(path.read_bytes)
        try:
            result = await run_in_threadpool(
                use_case.execute, principal.subject, data, filename, None, filename
            )
        except NotAPdfError:
            return JSONResponse({"rejected": "not_a_pdf"})
        except (TooLargeError, QuotaExceededError, UploadRejectedError) as exc:
            return JSONResponse({"rejected": type(exc).__name__})
        return JSONResponse(
            {"document_id": result.document.id, "duplicate_of": result.duplicate_of}
        )
    finally:
        await run_in_threadpool(_discard, directory, upload_id)
