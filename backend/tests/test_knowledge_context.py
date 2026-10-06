from __future__ import annotations

from uuid import UUID, uuid5

import pytest

from app.application.knowledge.context_builder import RAGContextBuilder
from app.domain.knowledge import (
    KnowledgeChunk,
    KnowledgeMetadata,
    KnowledgeSearchResult,
)


TEST_NAMESPACE = UUID("00000000-0000-0000-0000-000000000001")


def _uuid(value: str) -> UUID:
    """
    Convert a human-readable test identifier into a deterministic UUID.

    The production domain model requires UUID values, so tests should use
    valid UUIDs rather than placeholder strings such as "chunk-1".
    """
    return uuid5(TEST_NAMESPACE, value)


def _metadata(
    title: str = "VPN Troubleshooting",
) -> KnowledgeMetadata:
    return KnowledgeMetadata(
        source_type="markdown",
        category="network",
        subcategory="vpn",
        title=title,
        document_id="vpn-troubleshooting",
        version="1",
        language="en",
        access_level="internal",
        tags=["vpn", "troubleshooting"],
    )


def _result(
    *,
    chunk_id: str,
    content: str,
    score: float,
    chunk_index: int = 0,
    title: str = "VPN Troubleshooting",
    retrieval_method: str = "hybrid",
) -> KnowledgeSearchResult:
    """
    Build a valid KnowledgeSearchResult for context-builder tests.

    The domain model requires UUID identifiers, therefore the readable
    test identifiers are deterministically converted into UUIDs.
    """

    chunk = KnowledgeChunk(
        id=_uuid(chunk_id),
        document_id=_uuid("document-1"),
        content=content,
        chunk_index=chunk_index,
        heading_path=["VPN Troubleshooting"],
        metadata=_metadata(title),
    )

    return KnowledgeSearchResult(
        chunk=chunk,
        score=score,
        retrieval_method=retrieval_method,
    )


def test_builds_context_from_retrieval_results() -> None:
    builder = RAGContextBuilder()

    results = [
        _result(
            chunk_id="chunk-1",
            content="Restart the VPN client.",
            score=1.0,
        ),
        _result(
            chunk_id="chunk-2",
            content="Verify corporate credentials.",
            score=0.8,
            chunk_index=1,
        ),
    ]

    context = builder.build(
        query="VPN authentication failure",
        results=results,
    )

    assert context.query == "VPN authentication failure"

    assert len(context.items) == 2

    assert context.items[0].content == "Restart the VPN client."
    assert context.items[1].content == "Verify corporate credentials."

    assert context.items[0].score == 1.0
    assert context.items[1].score == 0.8


def test_context_preserves_retrieval_order() -> None:
    builder = RAGContextBuilder()

    results = [
        _result(
            chunk_id="chunk-a",
            content="First result.",
            score=0.9,
        ),
        _result(
            chunk_id="chunk-b",
            content="Second result.",
            score=0.7,
        ),
    ]

    context = builder.build(
        query="VPN problem",
        results=results,
    )

    assert [item.content for item in context.items] == [
        "First result.",
        "Second result.",
    ]


def test_duplicate_chunks_are_removed() -> None:
    builder = RAGContextBuilder()

    results = [
        _result(
            chunk_id="chunk-1",
            content="Same chunk.",
            score=1.0,
        ),
        _result(
            chunk_id="chunk-1",
            content="Same chunk.",
            score=0.9,
        ),
        _result(
            chunk_id="chunk-2",
            content="Different chunk.",
            score=0.8,
        ),
    ]

    context = builder.build(
        query="VPN troubleshooting",
        results=results,
    )

    assert len(context.items) == 2

    assert [item.content for item in context.items] == [
        "Same chunk.",
        "Different chunk.",
    ]


def test_max_items_is_enforced() -> None:
    builder = RAGContextBuilder(
        max_items=2,
    )

    results = [
        _result(
            chunk_id="chunk-1",
            content="One",
            score=1.0,
        ),
        _result(
            chunk_id="chunk-2",
            content="Two",
            score=0.9,
        ),
        _result(
            chunk_id="chunk-3",
            content="Three",
            score=0.8,
        ),
    ]

    context = builder.build(
        query="VPN troubleshooting",
        results=results,
    )

    assert len(context.items) == 2

    assert [item.content for item in context.items] == [
        "One",
        "Two",
    ]


def test_empty_query_is_rejected() -> None:
    builder = RAGContextBuilder()

    with pytest.raises(ValueError, match="query"):
        builder.build(
            query="   ",
            results=[],
        )


def test_empty_results_produce_empty_context() -> None:
    builder = RAGContextBuilder()

    context = builder.build(
        query="VPN troubleshooting",
        results=[],
    )

    assert context.query == "VPN troubleshooting"
    assert context.items == ()