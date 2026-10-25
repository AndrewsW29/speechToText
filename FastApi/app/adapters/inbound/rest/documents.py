from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.adapters.inbound.rest.auth import Principal, require_principal
from app.adapters.inbound.rest.errors import ProblemError
from app.application.pdf.ports.document_repository import DocumentRepository
from app.application.pdf.services.validation import PdfLimits
from app.application.pdf.use_cases.upload_document import UploadDocument
from app.config import Settings
from app.container import Container
from app.domain.pdf.document import Document, DocumentStatus, public_reason

router = APIRouter(prefix="/v1/documents", tags=["documents"])


class DocumentAccepted(BaseModel):
    document_id: str
    status: str
    version: int
    duplicate_of: str | None


class DocumentOut(BaseModel):
    document_id: str
    title: str
    status: str
    version: int
    pages: int | None
    flags: list[str]
    failure_reason: str | None
    created_at: datetime


class DocumentList(BaseModel):
    items: list[DocumentOut]


def to_out(d: Document) -> DocumentOut:
    return DocumentOut(
        document_id=d.id,
        title=d.title,
        status=d.status.value,
        version=d.version,
        pages=d.pages,
        flags=list(d.flags),
        failure_reason=public_reason(d.failure_reason),
        created_at=d.created_at,
    )


def _upload_use_case(request: Request) -> UploadDocument:
    use_case = request.app.state.container.upload_document
    if use_case is None:
        raise ProblemError(503, "Document processing is not configured")
    return use_case  # type: ignore[no-any-return]


def repository(request: Request) -> DocumentRepository:
    repo = request.app.state.container.documents
    if repo is None:
        raise ProblemError(503, "Document processing is not configured")
    return repo  # type: ignore[no-any-return]


def owned_document(request: Request, document_id: str, principal: Principal) -> Document:
    """Documents of other users do not exist as far as you are concerned."""
    document = repository(request).get(document_id)
    if document is None or document.owner != principal.subject:
        raise ProblemError(404, "Document not found")
    return document


@router.post(
    "",
    response_model=DocumentAccepted,
    status_code=202,
    responses={
        200: {
            "description": "Duplicate: this owner already uploaded the same file",
            "model": DocumentAccepted,
        }
    },
)
async def upload(
    request: Request,
    file: Annotated[UploadFile, File()],
    principal: Annotated[Principal, Depends(require_principal)],
    title: Annotated[str | None, Form()] = None,
) -> JSONResponse:
    settings: Settings = request.app.state.settings
    limit = PdfLimits.from_settings(settings).max_file_bytes
    data = await file.read(limit + 1)  # stop reading as soon as the limit is exceeded
    result = await run_in_threadpool(
        _upload_use_case(request).execute,
        principal.subject,
        data,
        file.filename,
        file.content_type,
        title,
    )
    body = DocumentAccepted(
        document_id=result.document.id,
        status=result.document.status.value,
        version=result.document.version,
        duplicate_of=result.duplicate_of,
    )
    return JSONResponse(body.model_dump(), status_code=200 if result.duplicate_of else 202)


@router.get("", response_model=DocumentList)
async def list_documents(
    request: Request,
    principal: Annotated[Principal, Depends(require_principal)],
    status: Annotated[str | None, Query()] = None,
) -> DocumentList:
    try:
        wanted = DocumentStatus(status) if status else None
    except ValueError:
        raise ProblemError(422, "Unknown status filter") from None
    items = await run_in_threadpool(repository(request).list_for, principal.subject, wanted)
    return DocumentList(items=[to_out(d) for d in items])


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: str,
    request: Request,
    principal: Annotated[Principal, Depends(require_principal)],
) -> DocumentOut:
    return to_out(await run_in_threadpool(owned_document, request, document_id, principal))


__all__ = ["Container", "router"]
