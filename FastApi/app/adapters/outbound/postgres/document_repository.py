"""Sync SQLAlchemy repository for documents, pipeline steps and dead letters (workers are sync)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Engine,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.application.pdf.ports.document_repository import DocumentRepository, OwnerUsage, StepStore
from app.domain.pdf.document import Document, DocumentStatus


class Base(DeclarativeBase):
    """Declarative base for the document tables (kept apart from the async one on purpose)."""


class DocumentRow(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("owner", "sha256", name="uq_documents_owner_sha256"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    owner: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(200))
    sha256: Mapped[str] = mapped_column(String(64))
    object_key: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DocumentVersionRow(Base):
    __tablename__ = "document_versions"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    sha256: Mapped[str] = mapped_column(String(64))
    object_key: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class IngestStepRow(Base):
    __tablename__ = "ingest_steps"

    key: Mapped[str] = mapped_column(String(300), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(32), index=True)
    result: Mapped[dict[str, Any]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DeadLetterRow(Base):
    __tablename__ = "dead_letters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(32), index=True)
    reason: Mapped[str] = mapped_column(String(200))
    attempts: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def create_schema(engine: Engine) -> None:
    """For tests and local SQLite; production schemas come from Alembic migrations."""
    Base.metadata.create_all(engine)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _to_row(d: Document) -> DocumentRow:
    return DocumentRow(
        id=d.id,
        owner=d.owner,
        title=d.title,
        sha256=d.sha256,
        object_key=d.object_key,
        status=d.status.value,
        version=d.version,
        pages=d.pages,
        flags=list(d.flags),
        failure_reason=d.failure_reason,
        size_bytes=d.size_bytes,
        created_at=d.created_at,
    )


def _to_domain(r: DocumentRow) -> Document:
    return Document(
        id=r.id,
        owner=r.owner,
        title=r.title,
        sha256=r.sha256,
        object_key=r.object_key,
        status=DocumentStatus(r.status),
        version=r.version,
        pages=r.pages,
        flags=tuple(r.flags or ()),
        failure_reason=r.failure_reason,
        size_bytes=int(r.size_bytes or 0),
        created_at=_aware(r.created_at),
    )


class SqlDocumentRepository(DocumentRepository, StepStore):
    def __init__(self, engine: Engine) -> None:
        self._sessions = sessionmaker(engine, expire_on_commit=False)

    def _session(self) -> Session:
        return self._sessions()

    def add(self, document: Document) -> None:
        with self._session() as s, s.begin():
            s.add(_to_row(document))
            s.add(
                DocumentVersionRow(
                    document_id=document.id,
                    version=document.version,
                    sha256=document.sha256,
                    object_key=document.object_key,
                    created_at=document.created_at,
                )
            )

    def get(self, document_id: str) -> Document | None:
        with self._session() as s:
            row = s.get(DocumentRow, document_id)
            return _to_domain(row) if row else None

    def find_by_hash(self, owner: str, sha256: str) -> Document | None:
        with self._session() as s:
            row = s.scalars(
                select(DocumentRow).where(DocumentRow.owner == owner, DocumentRow.sha256 == sha256)
            ).first()
            return _to_domain(row) if row else None

    def list_for(self, owner: str, status: DocumentStatus | None = None) -> Sequence[Document]:
        query = (
            select(DocumentRow)
            .where(DocumentRow.owner == owner)
            .order_by(DocumentRow.created_at.desc())
        )
        if status is not None:
            query = query.where(DocumentRow.status == status.value)
        with self._session() as s:
            return [_to_domain(r) for r in s.scalars(query)]

    def save(self, document: Document) -> None:
        with self._session() as s, s.begin():
            row = s.get(DocumentRow, document.id)
            if row is None:
                raise LookupError(document.id)
            for key, value in {
                "title": document.title,
                "status": document.status.value,
                "version": document.version,
                "pages": document.pages,
                "flags": list(document.flags),
                "failure_reason": document.failure_reason,
                "size_bytes": document.size_bytes,
            }.items():
                setattr(row, key, value)

    def usage(self, owner: str) -> OwnerUsage:
        start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        with self._session() as s:
            docs, storage = s.execute(
                select(
                    func.count(DocumentRow.id), func.coalesce(func.sum(DocumentRow.size_bytes), 0)
                ).where(DocumentRow.owner == owner)
            ).one()
            pages = s.scalar(
                select(func.coalesce(func.sum(DocumentRow.pages), 0)).where(
                    DocumentRow.owner == owner, DocumentRow.created_at >= start
                )
            )
        return OwnerUsage(int(docs), int(pages or 0), int(storage))

    def dead_letter(self, document_id: str, reason: str, attempts: int) -> None:
        with self._session() as s, s.begin():
            s.add(
                DeadLetterRow(
                    document_id=document_id,
                    reason=reason[:200],
                    attempts=attempts,
                    created_at=datetime.now(UTC),
                )
            )

    def dead_letter_rows(self) -> list[tuple[str, str, int]]:
        with self._session() as s:
            return [
                (r.document_id, r.reason, r.attempts)
                for r in s.scalars(select(DeadLetterRow).order_by(DeadLetterRow.id))
            ]

    def get_step(self, key: str) -> dict[str, Any] | None:
        with self._session() as s:
            row = s.get(IngestStepRow, key)
            return dict(row.result) if row else None

    def put_step(self, key: str, document_id: str, result: dict[str, Any]) -> None:
        with self._session() as s, s.begin():
            row = s.get(IngestStepRow, key)
            if row is None:
                s.add(
                    IngestStepRow(
                        key=key,
                        document_id=document_id,
                        result=result,
                        updated_at=datetime.now(UTC),
                    )
                )
            else:
                row.result, row.updated_at = result, datetime.now(UTC)
