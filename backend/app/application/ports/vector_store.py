from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.domain.knowledge import (
    KnowledgeChunk,
    KnowledgeSearchResult,
)


class VectorStore(ABC):
    """
    Application port for knowledge storage and retrieval.

    The application layer knows only about these operations.
    Infrastructure implementations decide how they are performed.

    Current implementation:
        QdrantVectorStore
    """

    @abstractmethod
    def upsert(
        self,
        chunks: list[KnowledgeChunk],
        embeddings: list[list[float]],
    ) -> None:
        """
        Store or replace knowledge chunks and their embeddings.
        """
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[KnowledgeSearchResult]:
        """
        Dense semantic retrieval.
        """
        raise NotImplementedError

    @abstractmethod
    def keyword_search(
        self,
        query: str,
        *,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[KnowledgeSearchResult]:
        """
        Lexical/BM25 retrieval.
        """
        raise NotImplementedError

    @abstractmethod
    def hybrid_search(
        self,
        query_embedding: list[float],
        query_text: str,
        *,
        limit: int = 5,
        candidate_limit: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[KnowledgeSearchResult]:
        """
        Hybrid dense + lexical retrieval.

        The infrastructure implementation is responsible for
        candidate generation and fusion.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_document(
        self,
        document_id: str,
    ) -> None:
        """
        Delete all chunks belonging to a logical document.
        """
        raise NotImplementedError