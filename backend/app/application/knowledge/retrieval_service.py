from __future__ import annotations

from typing import Any, Literal

from app.application.ports.embedding_provider import EmbeddingProvider
from app.application.ports.vector_store import VectorStore
from app.domain.knowledge import KnowledgeSearchResult


RetrievalMode = Literal["dense", "bm25", "hybrid"]


class KnowledgeRetrievalService:
    """
    Application service for enterprise knowledge retrieval.

    Responsibilities:

        1. Validate the user query.
        2. Generate query embeddings when required.
        3. Select the retrieval strategy.
        4. Delegate retrieval to the VectorStore port.

    Retrieval mechanics remain inside the infrastructure adapter.

    Flow:

        User Query
            |
            v
        Retrieval Service
            |
            +-------------------+
            |                   |
            v                   v
        EmbeddingProvider   raw query
            |                   |
            +---------+---------+
                      |
                      v
                  VectorStore
                      |
                      v
             KnowledgeSearchResult[]
    """

    MAX_LIMIT = 100

    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    # ------------------------------------------------------------------
    # Dense retrieval
    # ------------------------------------------------------------------

    def dense_search(
        self,
        query: str,
        *,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[KnowledgeSearchResult]:
        """
        Semantic/dense retrieval.

        Query
            -> embedding provider
            -> dense vector
            -> vector store
        """

        query = self._validate_query(query)
        limit = self._validate_limit(limit)

        embedding = self._embedding_provider.embed_query(
            query
        )

        return self._vector_store.search(
            embedding,
            limit=limit,
            filters=filters,
        )

    # ------------------------------------------------------------------
    # BM25 retrieval
    # ------------------------------------------------------------------

    def keyword_search(
        self,
        query: str,
        *,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[KnowledgeSearchResult]:
        """
        Lexical/BM25 retrieval.

        The application passes the raw query to the vector-store
        implementation. Qdrant handles the BM25 representation.
        """

        query = self._validate_query(query)
        limit = self._validate_limit(limit)

        return self._vector_store.keyword_search(
            query,
            limit=limit,
            filters=filters,
        )

    # ------------------------------------------------------------------
    # Hybrid retrieval
    # ------------------------------------------------------------------

    def hybrid_search(
        self,
        query: str,
        *,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
        candidate_limit: int | None = None,
    ) -> list[KnowledgeSearchResult]:
        """
        Hybrid retrieval.

        Query
            |
            +--> dense embedding
            |
            +--> raw query for BM25
            |
            v
        VectorStore
            |
            v
        Dense + BM25 + RRF
        """

        query = self._validate_query(query)
        limit = self._validate_limit(limit)

        if candidate_limit is not None:
            candidate_limit = self._validate_limit(
                candidate_limit
            )

        embedding = self._embedding_provider.embed_query(
            query
        )

        # IMPORTANT:
        #
        # Do not pass candidate_limit when it is None.
        #
        # This keeps the application contract compatible with
        # lightweight test doubles and implementations that use
        # their own default candidate depth.
        #
        # The production Qdrant adapter still supports candidate_limit.

        if candidate_limit is None:
            return self._vector_store.hybrid_search(
                query_embedding=embedding,
                query_text=query,
                limit=limit,
                filters=filters,
            )

        return self._vector_store.hybrid_search(
            query_embedding=embedding,
            query_text=query,
            limit=limit,
            candidate_limit=candidate_limit,
            filters=filters,
        )

    # ------------------------------------------------------------------
    # Unified retrieval API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        mode: RetrievalMode = "hybrid",
        limit: int = 5,
        filters: dict[str, Any] | None = None,
        candidate_limit: int | None = None,
    ) -> list[KnowledgeSearchResult]:
        """
        Unified retrieval entry point.

        Supported modes:

            dense
            bm25
            hybrid

        Hybrid is the default.
        """

        query = self._validate_query(query)
        mode = mode.strip().lower()

        if mode == "dense":
            return self.dense_search(
                query,
                limit=limit,
                filters=filters,
            )

        if mode == "bm25":
            return self.keyword_search(
                query,
                limit=limit,
                filters=filters,
            )

        if mode == "hybrid":
            return self.hybrid_search(
                query,
                limit=limit,
                filters=filters,
                candidate_limit=candidate_limit,
            )

        raise ValueError(
            "mode must be one of: hybrid, dense, bm25"
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_query(
        query: str,
    ) -> str:
        if not isinstance(query, str):
            raise ValueError(
                "query must be a string"
            )

        query = query.strip()

        if not query:
            raise ValueError(
                "query cannot be empty"
            )

        return query

    @classmethod
    def _validate_limit(
        cls,
        limit: int,
    ) -> int:
        if limit < 1:
            raise ValueError(
                "limit must be greater than zero"
            )

        if limit > cls.MAX_LIMIT:
            raise ValueError(
                f"limit cannot be greater than {cls.MAX_LIMIT}"
            )

        return limit