from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.knowledge.retrieval_service import (
    KnowledgeRetrievalService,
)
from app.domain.knowledge import (
    KnowledgeChunk,
    KnowledgeMetadata,
)


class FakeEmbeddingProvider:
    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        return [1.0, 0.0, 0.0]


class FakeVectorStore:
    def __init__(self) -> None:
        metadata = KnowledgeMetadata(
            category="network",
            subcategory="vpn",
            title="VPN Troubleshooting",
            document_id="vpn-troubleshooting",
            tags=[
                "vpn",
                "network",
            ],
        )

        self.chunk = KnowledgeChunk(
            document_id=uuid4(),
            content=(
                "Restart the corporate VPN client "
                "and reconnect."
            ),
            chunk_index=0,
            metadata=metadata,
        )

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int,
        filters: dict | None = None,
    ):
        from app.domain.knowledge import (
            KnowledgeSearchResult,
        )

        return [
            KnowledgeSearchResult(
                chunk=self.chunk,
                score=0.91,
                retrieval_method="dense",
            )
        ][:limit]

    def keyword_search(
        self,
        query: str,
        *,
        limit: int,
        filters: dict | None = None,
    ):
        from app.domain.knowledge import (
            KnowledgeSearchResult,
        )

        return [
            KnowledgeSearchResult(
                chunk=self.chunk,
                score=3.42,
                retrieval_method="bm25",
            )
        ][:limit]

    def hybrid_search(
        self,
        query_embedding: list[float],
        query_text: str,
        *,
        limit: int,
        filters: dict | None = None,
    ):
        from app.domain.knowledge import (
            KnowledgeSearchResult,
        )

        return [
            KnowledgeSearchResult(
                chunk=self.chunk,
                score=0.8333,
                retrieval_method="hybrid",
            )
        ][:limit]


@pytest.fixture
def service() -> KnowledgeRetrievalService:
    return KnowledgeRetrievalService(
        embedding_provider=(
            FakeEmbeddingProvider()
        ),
        vector_store=FakeVectorStore(),
    )


def test_dense_search(
    service: KnowledgeRetrievalService,
) -> None:
    results = service.dense_search(
        "How do I troubleshoot VPN?",
        limit=3,
    )

    assert len(results) == 1
    assert (
        results[0].retrieval_method
        == "dense"
    )


def test_bm25_search(
    service: KnowledgeRetrievalService,
) -> None:
    results = service.keyword_search(
        "VPN client",
        limit=3,
    )

    assert len(results) == 1
    assert (
        results[0].retrieval_method
        == "bm25"
    )


def test_hybrid_search(
    service: KnowledgeRetrievalService,
) -> None:
    results = service.hybrid_search(
        "How do I troubleshoot VPN?",
        limit=3,
    )

    assert len(results) == 1
    assert (
        results[0].retrieval_method
        == "hybrid"
    )


def test_unified_search_defaults_to_hybrid(
    service: KnowledgeRetrievalService,
) -> None:
    results = service.search(
        "How do I troubleshoot VPN?"
    )

    assert len(results) == 1
    assert (
        results[0].retrieval_method
        == "hybrid"
    )


def test_unified_search_supports_dense(
    service: KnowledgeRetrievalService,
) -> None:
    results = service.search(
        "How do I troubleshoot VPN?",
        mode="dense",
    )

    assert (
        results[0].retrieval_method
        == "dense"
    )


def test_unified_search_supports_bm25(
    service: KnowledgeRetrievalService,
) -> None:
    results = service.search(
        "VPN client",
        mode="bm25",
    )

    assert (
        results[0].retrieval_method
        == "bm25"
    )


def test_empty_query_is_rejected(
    service: KnowledgeRetrievalService,
) -> None:
    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        service.search("   ")


def test_invalid_mode_is_rejected(
    service: KnowledgeRetrievalService,
) -> None:
    with pytest.raises(
        ValueError,
        match="mode must be one of",
    ):
        service.search(
            "VPN",
            mode="invalid",
        )