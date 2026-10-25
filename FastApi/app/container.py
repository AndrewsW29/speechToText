"""Dependency container produced by the composition root (app.main)."""

from dataclasses import dataclass

from app.application.ports.ingestion_jobs import IngestionJobs
from app.application.use_cases.ask_question import AskQuestion


@dataclass(frozen=True, slots=True)
class Container:
    ask_question: AskQuestion
    ingestion: IngestionJobs | None = None
