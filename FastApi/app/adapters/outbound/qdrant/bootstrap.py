"""Idempotent collection bootstrap for `code_knowledge`."""

from __future__ import annotations

from qdrant_client import QdrantClient, models

DENSE = "dense"
SPARSE = "bm25"
PAYLOAD_INDEXES = ("language", "framework", "artifact_type")


def ensure_collection(client: QdrantClient, name: str, dimension: int) -> None:
    """Create the hybrid collection (dense cosine + sparse BM25-style IDF) if it is missing."""
    if client.collection_exists(name):
        return
    client.create_collection(
        collection_name=name,
        vectors_config={
            DENSE: models.VectorParams(size=dimension, distance=models.Distance.COSINE)
        },
        sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )
    for field in PAYLOAD_INDEXES:
        client.create_payload_index(name, field, models.PayloadSchemaType.KEYWORD)
