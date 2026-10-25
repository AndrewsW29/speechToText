from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.adapters.inbound.rest.auth import Principal, require_role
from app.adapters.inbound.rest.errors import ProblemError
from app.application.ports.ingestion_jobs import IngestionJobs
from app.container import Container

router = APIRouter(prefix="/v1/ingestions", tags=["ingestions"])
INGEST_ROLE = "ingest"


class IngestionRequest(BaseModel):
    url: str = Field(max_length=2048)
    language: str = Field(default="java", min_length=1, max_length=20)
    framework: str | None = Field(default=None, max_length=40)

    @field_validator("url")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("url must not be blank")
        return value.strip()


class IngestionAccepted(BaseModel):
    job_id: str
    status_url: str


class IngestionStatus(BaseModel):
    job_id: str
    state: str
    documents: int
    chunks: int
    error: str | None


def _jobs(request: Request) -> IngestionJobs:
    container: Container = request.app.state.container
    if container.ingestion is None:
        raise ProblemError(503, "Ingestion is not configured")
    return container.ingestion


@router.post("", status_code=202, response_model=IngestionAccepted)
async def submit(
    body: IngestionRequest,
    request: Request,
    _: Annotated[Principal, Depends(require_role(INGEST_ROLE))],
) -> JSONResponse:
    job_id = _jobs(request).submit(body.url, body.language, body.framework)
    location = f"/v1/ingestions/{job_id}"
    return JSONResponse(
        {"job_id": job_id, "status_url": location}, status_code=202, headers={"Location": location}
    )


@router.get("/{job_id}", response_model=IngestionStatus)
async def status(
    job_id: str,
    request: Request,
    _: Annotated[Principal, Depends(require_role(INGEST_ROLE))],
) -> IngestionStatus:
    job = _jobs(request).status(job_id)
    if job is None:
        raise ProblemError(404, "Ingestion job not found")
    return IngestionStatus(
        job_id=job.id, state=job.state, documents=job.documents, chunks=job.chunks, error=job.error
    )
