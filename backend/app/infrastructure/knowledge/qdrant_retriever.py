from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from qdrant_client import QdrantClient, models


RetrievalMode = Literal["dense", "bm25", "hybrid"]


@dataclass(frozen=True)
class RetrievedChunk:
    """
    Normalized representation of a chunk returned by Qdrant.

    The application layer should not need to know anything about
    Qdrant's Record/ScoredPoint structures.
    """

    id: str
    content: str
    score: float
    document_id: str
    chunk_index: int
    heading_path: list[str]
    metadata: dict[str, Any]


class QdrantKnowledgeRetriever:
    """
    Infrastructure adapter for knowledge retrieval.

    Responsibilities:
    - Execute dense retrieval.
    - Execute BM25 retrieval.
    - Execute hybrid dense + BM25 retrieval.
    - Convert Qdrant results into application-friendly objects.

    Does NOT:
    - build prompts
    - call an LLM
    - assemble final RAG context
    - make business decisions
    """

    DENSE_VECTOR_NAME = "dense"
    BM25_VECTOR_NAME = "bm25"

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str = "itsm_knowledge_v2",
    ) -> None:
        self._client = client
        self._collection_name = collection_name

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        mode: RetrievalMode = "hybrid",
        limit: int = 5,
        candidate_limit: int | None = None,
    ) -> list[RetrievedChunk]:
        """
        Unified retrieval entry point.

        mode:
            dense  -> semantic retrieval
            bm25   -> lexical retrieval
            hybrid -> dense + BM25 + RRF

        Hybrid is the default because the knowledge system should
        benefit from both semantic and exact keyword matching.
        """

        normalized_query = query.strip()

        if not normalized_query:
            raise ValueError("query must not be empty")

        if mode not in {"dense", "bm25", "hybrid"}:
            raise ValueError(
                f"unsupported retrieval mode: {mode}"
            )

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        candidate_limit = candidate_limit or max(limit * 4, 20)

        if mode == "dense":
            return self._dense_search(
                normalized_query,
                limit=limit,
            )

        if mode == "bm25":
            return self._bm25_search(
                normalized_query,
                limit=limit,
            )

        return self._hybrid_search(
            normalized_query,
            limit=limit,
            candidate_limit=candidate_limit,
        )

    # ------------------------------------------------------------------
    # Dense retrieval
    # ------------------------------------------------------------------

    def _dense_search(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[RetrievedChunk]:
        """
        Dense semantic retrieval.

        The dense embedding is generated locally by the application's
        embedding component before this adapter is called.
        """

        query_vector = self._build_dense_query_vector(query)

        response = self._client.query_points(
            collection_name=self._collection_name,
            query=query_vector,
            using=self.DENSE_VECTOR_NAME,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        return [
            self._to_retrieved_chunk(point)
            for point in response.points
        ]

    # ------------------------------------------------------------------
    # BM25 retrieval
    # ------------------------------------------------------------------

    def _bm25_search(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[RetrievedChunk]:
        """
        Lexical retrieval using Qdrant's BM25 sparse vector.

        Qdrant supports its BM25 model directly through Document(),
        avoiding a separate client-side BM25 implementation.
        """

        response = self._client.query_points(
            collection_name=self._collection_name,
            query=models.Document(
                text=query,
                model="Qdrant/bm25",
            ),
            using=self.BM25_VECTOR_NAME,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        return [
            self._to_retrieved_chunk(point)
            for point in response.points
        ]

    # ------------------------------------------------------------------
    # Hybrid retrieval
    # ------------------------------------------------------------------

    def _hybrid_search(
        self,
        query: str,
        *,
        limit: int,
        candidate_limit: int,
    ) -> list[RetrievedChunk]:
        """
        Dense + BM25 hybrid retrieval using Qdrant RRF.

        Each retriever produces a candidate set.
        Qdrant then combines their rankings using Reciprocal Rank
        Fusion.
        """

        dense_vector = self._build_dense_query_vector(query)

        response = self._client.query_points(
            collection_name=self._collection_name,
            prefetch=[
                models.Prefetch(
                    query=dense_vector,
                    using=self.DENSE_VECTOR_NAME,
                    limit=candidate_limit,
                ),
                models.Prefetch(
                    query=models.Document(
                        text=query,
                        model="Qdrant/bm25",
                    ),
                    using=self.BM25_VECTOR_NAME,
                    limit=candidate_limit,
                ),
            ],
            query=models.FusionQuery(
                fusion=models.Fusion.RRF,
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        return [
            self._to_retrieved_chunk(point)
            for point in response.points
        ]

    # ------------------------------------------------------------------
    # Dense embedding boundary
    # ------------------------------------------------------------------

    def _build_dense_query_vector(
        self,
        query: str,
    ) -> list[float]:
        """
        Generate the dense query embedding.

        IMPORTANT:
        This method is intentionally isolated.

        Replace the implementation with the same embedding model
        used during ingestion.

        Keeping this boundary isolated means the Qdrant adapter does
        not become coupled to a particular embedding library.
        """

        raise NotImplementedError(
            "Connect the production dense embedding provider here."
        )

    # ------------------------------------------------------------------
    # Qdrant -> application mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _to_retrieved_chunk(
        point: Any,
    ) -> RetrievedChunk:
        payload = point.payload or {}

        metadata = payload.get("metadata") or {}

        return RetrievedChunk(
            id=str(point.id),
            content=str(
                payload.get("content") or ""
            ),
            score=float(
                point.score or 0.0
            ),
            document_id=str(
                payload.get("document_id")
                or metadata.get("document_id")
                or ""
            ),
            chunk_index=int(
                payload.get("chunk_index") or 0
            ),
            heading_path=list(
                payload.get("heading_path") or []
            ),
            metadata=dict(metadata),
        )