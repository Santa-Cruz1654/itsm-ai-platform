from __future__ import annotations

import os
from typing import Any

from qdrant_client import QdrantClient, models

from app.application.ports.vector_store import VectorStore
from app.domain.knowledge import (
    KnowledgeChunk,
    KnowledgeMetadata,
    KnowledgeSearchResult,
)


class QdrantVectorStore(VectorStore):
    """
    Qdrant-backed knowledge vector store.

    Each knowledge chunk is stored as one Qdrant point containing:

        - dense semantic vector
        - BM25 sparse vector
        - knowledge metadata
        - chunk content

    Retrieval supports:

        - dense semantic search
        - BM25 lexical search
        - hybrid dense + BM25 search using RRF

    Qdrant itself generates the BM25 sparse representation using
    the Qdrant/bm25 inference model.
    """

    DENSE_VECTOR_NAME = "dense"
    BM25_VECTOR_NAME = "bm25"

    BM25_MODEL = "Qdrant/bm25"

    DEFAULT_COLLECTION_NAME = "itsm_knowledge_v2"

    MAX_LIMIT = 100

    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        collection_name: str | None = None,
        embedding_dimension: int = 768,
    ) -> None:
        url = url or os.getenv(
            "QDRANT_URL",
            "http://localhost:6333",
        )

        api_key = api_key or os.getenv(
            "QDRANT_API_KEY",
        )

        collection_name = (
            collection_name
            or os.getenv(
                "QDRANT_COLLECTION",
                self.DEFAULT_COLLECTION_NAME,
            )
        )

        self._collection_name = collection_name

        self._client = QdrantClient(
            url=url,
            api_key=api_key,
        )

        self._embedding_dimension = embedding_dimension

    # ==================================================================
    # Collection lifecycle
    # ==================================================================

    def ensure_collection(self) -> None:
        """
        Ensure the hybrid knowledge collection exists.

        Collection structure:

            dense -> dense semantic vector
            bm25  -> sparse BM25 vector
        """

        if self._client.collection_exists(
            self._collection_name
        ):
            self._create_payload_indexes()
            return

        self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config={
                self.DENSE_VECTOR_NAME: models.VectorParams(
                    size=self._embedding_dimension,
                    distance=models.Distance.COSINE,
                )
            },
            sparse_vectors_config={
                self.BM25_VECTOR_NAME: models.SparseVectorParams(
                    modifier=models.Modifier.IDF,
                )
            },
        )

        self._create_payload_indexes()

    def _create_payload_indexes(self) -> None:
        """
        Create payload indexes required for metadata filtering.
        """

        keyword_fields = [
            "document_id",
            "metadata.source_type",
            "metadata.category",
            "metadata.subcategory",
            "metadata.document_id",
            "metadata.version",
            "metadata.language",
            "metadata.access_level",
        ]

        for field in keyword_fields:
            try:
                self._client.create_payload_index(
                    collection_name=self._collection_name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
            except Exception:
                # Index may already exist.
                pass

    # ==================================================================
    # Ingestion
    # ==================================================================

    def upsert(
        self,
        chunks: list[KnowledgeChunk],
        embeddings: list[list[float]],
    ) -> None:
        """
        Store knowledge chunks in Qdrant.

        Every point receives:

            dense -> supplied embedding
            bm25  -> Qdrant-generated BM25 sparse representation
            payload -> chunk + metadata

        Deterministic chunk IDs make ingestion idempotent.
        """

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Chunk and embedding counts must match."
            )

        if not chunks:
            return

        self.ensure_collection()

        points: list[models.PointStruct] = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
            strict=True,
        ):
            points.append(
                models.PointStruct(
                    id=str(chunk.id),
                    vector={
                        self.DENSE_VECTOR_NAME: embedding,
                        self.BM25_VECTOR_NAME: models.Document(
                            text=self._bm25_text(chunk),
                            model=self.BM25_MODEL,
                        ),
                    },
                    payload={
                        "content": chunk.content,
                        "document_id": str(
                            chunk.document_id
                        ),
                        "chunk_index": chunk.chunk_index,
                        "heading_path": chunk.heading_path,
                        "metadata": chunk.metadata.model_dump(
                            mode="json"
                        ),
                    },
                )
            )

        self._client.upsert(
            collection_name=self._collection_name,
            points=points,
            wait=True,
        )

    # ==================================================================
    # Document deletion
    # ==================================================================

    def delete_document(
        self,
        document_id: str,
    ) -> None:
        """
        Delete every chunk belonging to one logical document.
        """

        document_id = document_id.strip()

        if not document_id:
            raise ValueError(
                "document_id cannot be empty."
            )

        self.ensure_collection()

        self._client.delete(
            collection_name=self._collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(
                                value=document_id
                            ),
                        )
                    ]
                )
            ),
            wait=True,
        )

    # ==================================================================
    # Dense retrieval
    # ==================================================================

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

        self._validate_limit(limit)

        self.ensure_collection()

        query_filter = self._build_filter(
            filters
        )

        response = self._client.query_points(
            collection_name=self._collection_name,
            query=query_embedding,
            using=self.DENSE_VECTOR_NAME,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        return [
            self._point_to_search_result(
                point,
                retrieval_method="dense",
            )
            for point in response.points
        ]

    # ==================================================================
    # BM25 retrieval
    # ==================================================================

    def keyword_search(
        self,
        query: str,
        *,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[KnowledgeSearchResult]:
        """
        Native Qdrant BM25 lexical retrieval.

        The query text is converted into a sparse BM25 query by Qdrant.
        """

        query = self._validate_query(query)

        self._validate_limit(limit)

        self.ensure_collection()

        query_filter = self._build_filter(
            filters
        )

        response = self._client.query_points(
            collection_name=self._collection_name,
            query=models.Document(
                text=query,
                model=self.BM25_MODEL,
            ),
            using=self.BM25_VECTOR_NAME,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        return [
            self._point_to_search_result(
                point,
                retrieval_method="bm25",
            )
            for point in response.points
        ]

    # ==================================================================
    # Hybrid retrieval
    # ==================================================================

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
        Hybrid retrieval:

            query
              |
              +----------------------+
              |                      |
              v                      v
           Dense                  BM25
              |                      |
              +----------+-----------+
                         |
                         v
                        RRF
                         |
                         v
                  final ranking

        Qdrant performs the fusion.
        """

        query_text = self._validate_query(
            query_text
        )

        self._validate_limit(limit)

        self.ensure_collection()

        if candidate_limit is None:
            candidate_limit = max(
                limit * 4,
                20,
            )

        self._validate_limit(
            candidate_limit
        )

        query_filter = self._build_filter(
            filters
        )

        response = self._client.query_points(
            collection_name=self._collection_name,

            prefetch=[
                models.Prefetch(
                    query=query_embedding,
                    using=self.DENSE_VECTOR_NAME,
                    limit=candidate_limit,
                    filter=query_filter,
                ),
                models.Prefetch(
                    query=models.Document(
                        text=query_text,
                        model=self.BM25_MODEL,
                    ),
                    using=self.BM25_VECTOR_NAME,
                    limit=candidate_limit,
                    filter=query_filter,
                ),
            ],

            query=models.FusionQuery(
                fusion=models.Fusion.RRF,
            ),

            limit=limit,
            with_payload=True,
        )

        return [
            self._point_to_search_result(
                point,
                retrieval_method="hybrid",
            )
            for point in response.points
        ]

    # ==================================================================
    # Internal mapping
    # ==================================================================

    @staticmethod
    def _point_to_search_result(
        point: models.ScoredPoint,
        *,
        retrieval_method: str,
    ) -> KnowledgeSearchResult:
        """
        Convert a Qdrant result into the domain result.
        """

        payload = point.payload or {}

        metadata = KnowledgeMetadata.model_validate(
            payload["metadata"]
        )

        chunk = KnowledgeChunk(
            id=point.id,
            document_id=payload["document_id"],
            content=payload["content"],
            chunk_index=payload["chunk_index"],
            heading_path=payload.get(
                "heading_path",
                [],
            ),
            metadata=metadata,
        )

        return KnowledgeSearchResult(
            chunk=chunk,
            score=float(point.score),
            retrieval_method=retrieval_method,
        )

    # ==================================================================
    # Filtering
    # ==================================================================

    @staticmethod
    def _build_filter(
        filters: dict[str, Any] | None,
    ) -> models.Filter | None:
        """
        Convert application-level filters into Qdrant filters.

        Examples:

            {"category": "vpn"}

        becomes:

            metadata.category == "vpn"

        While:

            {"document_id": "..."}

        targets the top-level document_id payload.
        """

        if not filters:
            return None

        conditions: list[
            models.FieldCondition
        ] = []

        for key, value in filters.items():

            if value is None:
                continue

            if key == "document_id":
                payload_key = "document_id"

            elif key.startswith("metadata."):
                payload_key = key

            else:
                payload_key = f"metadata.{key}"

            conditions.append(
                models.FieldCondition(
                    key=payload_key,
                    match=models.MatchValue(
                        value=value
                    ),
                )
            )

        if not conditions:
            return None

        return models.Filter(
            must=conditions
        )

    # ==================================================================
    # Validation
    # ==================================================================

    @staticmethod
    def _validate_query(
        query: str,
    ) -> str:
        query = query.strip()

        if not query:
            raise ValueError(
                "query cannot be empty."
            )

        return query

    @classmethod
    def _validate_limit(
        cls,
        limit: int,
    ) -> None:
        if limit < 1:
            raise ValueError(
                "limit must be greater than zero."
            )

        if limit > cls.MAX_LIMIT:
            raise ValueError(
                f"limit cannot be greater than "
                f"{cls.MAX_LIMIT}."
            )

    # ==================================================================
    # BM25 document text
    # ==================================================================

    @staticmethod
    def _bm25_text(
        chunk: KnowledgeChunk,
    ) -> str:
        """
        Text indexed by the BM25 sparse retriever.

        Content is the primary signal.

        Metadata is included so exact enterprise terminology
        such as:

            - article titles
            - categories
            - subcategories
            - tags
            - headings

        can participate in lexical retrieval.
        """

        return " ".join(
            [
                chunk.content,
                chunk.metadata.title,
                chunk.metadata.category,
                chunk.metadata.subcategory or "",
                " ".join(
                    chunk.metadata.tags
                ),
                " ".join(
                    chunk.heading_path
                ),
            ]
        )   