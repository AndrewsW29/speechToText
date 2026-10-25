from __future__ import annotations

from dataclasses import dataclass

from app.application.ports.document_source import DocumentSource
from app.application.ports.embedder import Embedder
from app.application.ports.vector_store import VectorWriter
from app.application.services.chunking import Chunker
from app.domain.entities import KnowledgeChunk
from app.domain.retrieval import Document, IndexedChunk, chunk_id


@dataclass(frozen=True, slots=True)
class IngestResult:
    chunks: int


@dataclass(frozen=True, slots=True)
class IngestSummary:
    documents: int
    chunks: int


class IngestDocument:
    """Chunk, embed and upsert one document. Content-hash ids make re-ingestion idempotent."""

    def __init__(
        self,
        embedder: Embedder,
        writer: VectorWriter,
        chunker: Chunker,
        code_chunker: Chunker | None = None,
    ) -> None:
        self._embedder = embedder
        self._writer = writer
        self._chunker = chunker
        self._code_chunker = code_chunker or chunker

    def execute(self, document: Document) -> IngestResult:
        chunker = self._code_chunker if document.content_type == "code" else self._chunker
        texts = chunker.chunk(document.text)
        if not texts:
            return IngestResult(chunks=0)
        embeddings = self._embedder.embed_many(texts)
        indexed = [
            IndexedChunk(
                KnowledgeChunk(
                    id=chunk_id(document.source_url, text),
                    text=text,
                    language=document.language,
                    framework=document.framework,
                    artifact_type=document.artifact_type,
                    source_url=document.source_url,
                ),
                embedding,
            )
            for text, embedding in zip(texts, embeddings, strict=True)
        ]
        self._writer.upsert(indexed)
        return IngestResult(chunks=len(indexed))


class IngestionFacade:
    """Simple entry point over fetch + ingest for a whole source."""

    def __init__(self, source: DocumentSource, ingest: IngestDocument) -> None:
        self._source = source
        self._ingest = ingest

    def ingest(
        self, url: str, language: str = "java", framework: str | None = None
    ) -> IngestSummary:
        if not url.strip():
            raise ValueError("url must not be blank")
        documents = self._source.fetch(url.strip(), language, framework)
        chunks = sum(self._ingest.execute(d).chunks for d in documents)
        return IngestSummary(documents=len(documents), chunks=chunks)
