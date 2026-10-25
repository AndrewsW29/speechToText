"""Server-Sent Events: stage updates for one document, resumable with Last-Event-ID."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.adapters.inbound.rest.auth import Principal, require_principal
from app.adapters.inbound.rest.documents import owned_document
from app.adapters.inbound.rest.errors import ProblemError
from app.application.pdf.ports.event_publisher import TERMINAL_STAGES
from app.config import Settings
from app.domain.pdf.document import public_reason

router = APIRouter(prefix="/v1/documents", tags=["documents"])
KEEPALIVE_EVERY = 40  # polls


def _public(event: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in event.items() if k != "reason"}
    if "reason" in event:
        out["reason"] = public_reason(str(event["reason"]))
    return out


@router.get(
    "/{document_id}/events",
    responses={
        200: {
            "description": "Stage events",
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
        }
    },
)
async def stream_events(
    document_id: str,
    request: Request,
    principal: Annotated[Principal, Depends(require_principal)],
    last_event_id: Annotated[str | None, Header()] = None,
) -> StreamingResponse:
    await run_in_threadpool(owned_document, request, document_id, principal)
    reader = request.app.state.container.document_events
    if reader is None:
        raise ProblemError(503, "Document events are not configured")
    settings: Settings = request.app.state.settings
    repo = request.app.state.container.documents
    after = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0

    async def generate() -> AsyncIterator[str]:
        cursor, idle = after, 0
        while not await request.is_disconnected():
            events = await run_in_threadpool(reader.read, document_id, cursor)
            for event in events:
                cursor = int(event["seq"])
                yield f"id: {cursor}\nevent: stage\ndata: {json.dumps(_public(event))}\n\n"
            if any(e["stage"] in TERMINAL_STAGES for e in events):
                return
            if not events:
                document = await run_in_threadpool(repo.get, document_id)
                if document is None or document.is_terminal:
                    return
                idle += 1
                if idle % KEEPALIVE_EVERY == 0:
                    yield ": keepalive\n\n"
            await asyncio.sleep(settings.pdf_events_poll_seconds)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
