from __future__ import annotations

from pathlib import Path
from typing import Any


class KnowledgeIngestionService:
    """
    Orchestrates the complete knowledge ingestion pipeline.

    Pipeline:

        source
          ↓
        document
          ↓
        chunks
          ↓
        embeddings
          ↓
        remove stale document chunks
          ↓
        deterministic upsert
    """

    def __init__(
        self,
        *,
        source: Any,
        embedding_provider: Any,
        vector_store: Any,
    ) -> None:
        self._source = source
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def ingest_directory(
        self,
        root: Path,
        chunker: Any,
    ) -> dict[str, int]:

        results: dict[str, int] = {}

        paths = self._source.list_documents(root)

        for path in paths:
            document = self._source.load(path)

            chunks = chunker.chunk(document)

            # Remove all previous chunks belonging to this logical
            # document before inserting the current representation.
            #
            # This guarantees that removed/changed chunks cannot
            # remain as stale points in Qdrant.
            self._vector_store.delete_document(
                str(document.id)
            )

            if not chunks:
                results[str(path)] = 0
                continue

            embeddings = (
                self._embedding_provider.embed_documents(
                    [
                        chunk.content
                        for chunk in chunks
                    ]
                )
            )

            self._vector_store.upsert(
                chunks=chunks,
                embeddings=embeddings,
            )

            results[str(path)] = len(chunks)

        return results