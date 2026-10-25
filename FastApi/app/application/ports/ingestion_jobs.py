from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JobStatus:
    id: str
    state: str  # queued | running | succeeded | failed
    documents: int = 0
    chunks: int = 0
    error: str | None = None


class IngestionJobs(ABC):
    """Inbound-facing port to run ingestion asynchronously and poll its status."""

    @abstractmethod
    def submit(self, url: str, language: str, framework: str | None) -> str: ...

    @abstractmethod
    def status(self, job_id: str) -> JobStatus | None: ...
