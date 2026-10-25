from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.adapters.inbound.rest.audio import ALLOWED_CONTENT_TYPES, detect_audio_format
from app.adapters.inbound.rest.auth import Principal, require_principal
from app.adapters.inbound.rest.errors import ProblemError
from app.config import Settings
from app.container import Container

router = APIRouter(prefix="/v1", tags=["questions"])


class TranscriptOut(BaseModel):
    text: str
    language: str | None


class SourceOut(BaseModel):
    id: str
    title: str
    url: str | None
    kind: str


class AnswerOut(BaseModel):
    text: str
    sources: list[SourceOut]


class IntentOut(BaseModel):
    name: str
    confidence: float
    entities: dict[str, str]


class ClarificationOut(BaseModel):
    question: str
    options: list[str]


class QuestionOut(BaseModel):
    """`status` is answer | clarify | abstain | command; only `answer` carries an answer."""

    status: str = "answer"
    question_id: str
    transcript: TranscriptOut
    answer: AnswerOut | None = None
    clarification: ClarificationOut | None = None
    message: str | None = None
    intent: IntentOut | None = None


@router.post("/questions", response_model=QuestionOut)
async def ask_question(
    request: Request,
    audio: Annotated[UploadFile, File()],
    _: Annotated[Principal, Depends(require_principal)],
    language: Annotated[str | None, Form()] = None,
) -> QuestionOut:
    settings: Settings = request.app.state.settings
    container: Container = request.app.state.container

    content_type = (audio.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ProblemError(
            415, "Unsupported media type", "Send audio/webm, ogg, mp4, aac, mpeg or wav"
        )

    data = await audio.read(settings.max_audio_bytes + 1)
    if len(data) > settings.max_audio_bytes:
        raise ProblemError(413, "Audio too large", f"Maximum is {settings.max_audio_bytes} bytes")
    if data and detect_audio_format(data) is None:
        raise ProblemError(
            415, "Unsupported media type", "Audio content does not match a supported format"
        )

    profile = {"LANGUAGE": settings.default_language} if settings.default_language else None
    result = await run_in_threadpool(container.ask_question.execute, data, language, profile)
    transcript = result.query.transcript
    return QuestionOut(
        status=result.status,
        question_id=result.query.id,
        transcript=TranscriptOut(
            text=transcript.text, language=transcript.language.code if transcript.language else None
        ),
        answer=(
            AnswerOut(
                text=result.answer.text,
                sources=[
                    SourceOut(id=s.id, title=s.title, url=s.url, kind=s.kind)
                    for s in result.answer.sources
                ],
            )
            if result.answer
            else None
        ),
        clarification=(
            ClarificationOut(
                question=result.clarification.question, options=result.clarification.options
            )
            if result.clarification
            else None
        ),
        message=result.message,
        intent=(
            IntentOut(
                name=result.intent.name,
                confidence=round(result.intent.confidence.value, 4),
                entities=dict(result.intent.entities),
            )
            if result.intent
            else None
        ),
    )
