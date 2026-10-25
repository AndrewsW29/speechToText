from abc import ABC, abstractmethod

from app.domain.retrieval import Document


class DocumentSource(ABC):
    """Outbound port: fetch documents to ingest from a URL."""

    @abstractmethod
    def fetch(
        self, url: str, language: str = "java", framework: str | None = None
    ) -> list[Document]: ...
