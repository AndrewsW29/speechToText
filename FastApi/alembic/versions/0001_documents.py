"""documents, document_versions, ingest_steps, dead_letters

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("owner", sa.String(128), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("object_key", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("pages", sa.Integer, nullable=True),
        sa.Column("flags", sa.JSON, nullable=False),
        sa.Column("failure_reason", sa.Text, nullable=True),
        sa.Column("size_bytes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner", "sha256", name="uq_documents_owner_sha256"),
    )
    op.create_index("ix_documents_owner", "documents", ["owner"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_table(
        "document_versions",
        sa.Column(
            "document_id",
            sa.String(32),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("version", sa.Integer, primary_key=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("object_key", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "ingest_steps",
        sa.Column("key", sa.String(300), primary_key=True),
        sa.Column("document_id", sa.String(32), nullable=False),
        sa.Column("result", sa.JSON, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ingest_steps_document_id", "ingest_steps", ["document_id"])
    op.create_table(
        "dead_letters",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(200), nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dead_letters_document_id", "dead_letters", ["document_id"])


def downgrade() -> None:
    for table in ("dead_letters", "ingest_steps", "document_versions", "documents"):
        op.drop_table(table)
