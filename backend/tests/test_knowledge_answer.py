from __future__ import annotations

from uuid import UUID

from app.application.knowledge.answer_service import (
    NO_GROUNDED_ANSWER,
    KnowledgeAnswerService,
)
from app.application.knowledge.context_assembly_service import (
    RAGContextAssemblyService,
)
from app.application.knowledge.rag_generation import (
    RAGGenerationService,
)
from app.domain.knowledge import (
    KnowledgeChunk,
    KnowledgeMetadata,
    KnowledgeSearchResult,
)


DOCUMENT_ID = UUID(
    "550e8400-e29b-41d4-a716-446655440000"
)


class FakeLLMProvider:
    def __init__(
        self,
        response: str = (
            "Use the Outlook troubleshooting steps."
        ),
    ) -> None:
        self.response = response
        self.prompts: list[str] = []

    def generate(
        self,
        prompt: str,
    ) -> str:
        self.prompts.append(prompt)
        return self.response


class FakeRetrievalService:
    def __init__(
        self,
        results: list[KnowledgeSearchResult],
    ) -> None:
        self.results = results
        self.queries: list[str] = []

    def hybrid_search(
        self,
        query: str,
        *,
        limit: int = 5,
        filters: dict[str, str] | None = None,
    ) -> list[KnowledgeSearchResult]:
        self.queries.append(query)
        return self.results[:limit]


def _result(
    *,
    chunk_id: str,
    score: float,
    content: str,
    chunk_index: int = 0,
    title: str = "Outlook Synchronization",
) -> KnowledgeSearchResult:
    metadata = KnowledgeMetadata(
        document_id=str(DOCUMENT_ID),
        title=title,
        source_type="markdown",
        category="outlook",
        subcategory="general",
        version="1",
        language="en",
        access_level="internal",
        tags=[
            "outlook",
            "synchronization",
        ],
    )

    chunk = KnowledgeChunk(
        id=UUID(chunk_id),
        document_id=DOCUMENT_ID,
        content=content,
        chunk_index=chunk_index,
        heading_path=[title],
        metadata=metadata,
    )

    return KnowledgeSearchResult(
        chunk=chunk,
        score=score,
        retrieval_method="hybrid",
    )


def _service(
    results: list[KnowledgeSearchResult],
    response: str = (
        "Use the Outlook troubleshooting steps."
    ),
) -> tuple[
    KnowledgeAnswerService,
    FakeLLMProvider,
    FakeRetrievalService,
]:
    retrieval = FakeRetrievalService(
        results
    )

    llm = FakeLLMProvider(
        response
    )

    service = KnowledgeAnswerService(
        retrieval_service=retrieval,
        context_assembly_service=(
            RAGContextAssemblyService()
        ),
        generation_service=(
            RAGGenerationService(
                llm_provider=llm,
            )
        ),
    )

    return (
        service,
        llm,
        retrieval,
    )


def test_relevant_question_returns_grounded_answer() -> None:
    service, llm, retrieval = _service(
        [
            _result(
                chunk_id=(
                    "550e8400-e29b-41d4-a716-446655440001"
                ),
                score=1.0,
                content=(
                    "Check Outlook connection status."
                ),
            ),
            _result(
                chunk_id=(
                    "550e8400-e29b-41d4-a716-446655440002"
                ),
                score=0.8,
                content=(
                    "Restart Outlook and allow "
                    "synchronization to complete."
                ),
                chunk_index=1,
            ),
        ]
    )

    result = service.ask(
        "How do I troubleshoot Outlook synchronization?"
    )

    assert result.grounded is True
    assert result.confidence == "high"
    assert (
        result.answer
        == "Use the Outlook troubleshooting steps."
    )
    assert len(result.sources) == 2

    assert retrieval.queries == [
        "How do I troubleshoot Outlook synchronization?"
    ]

    assert len(llm.prompts) == 1


def test_single_grounded_chunk_is_medium_confidence() -> None:
    service, _, _ = _service(
        [
            _result(
                chunk_id=(
                    "550e8400-e29b-41d4-a716-446655440003"
                ),
                score=0.8,
                content=(
                    "Check the Outlook connection status."
                ),
            )
        ]
    )

    result = service.ask(
        "Outlook is not synchronizing."
    )

    assert result.grounded is True
    assert result.confidence == "medium"
    assert len(result.sources) == 1


def test_weak_retrieval_does_not_generate() -> None:
    service, llm, _ = _service(
        [
            _result(
                chunk_id=(
                    "550e8400-e29b-41d4-a716-446655440004"
                ),
                score=0.4,
                content=(
                    "Unrelated enterprise information."
                ),
            )
        ]
    )

    result = service.ask(
        "How do I troubleshoot quantum hardware?"
    )

    assert result.grounded is False
    assert result.confidence == "low"
    assert result.answer == NO_GROUNDED_ANSWER
    assert result.sources == ()
    assert llm.prompts == []


def test_empty_retrieval_does_not_generate() -> None:
    service, llm, _ = _service([])

    result = service.ask(
        "How do I troubleshoot Outlook?"
    )

    assert result.grounded is False
    assert result.confidence == "low"
    assert result.sources == ()
    assert result.answer == NO_GROUNDED_ANSWER
    assert llm.prompts == []


def test_duplicate_chunks_are_not_returned_as_duplicate_sources() -> None:
    duplicate = _result(
        chunk_id=(
            "550e8400-e29b-41d4-a716-446655440005"
        ),
        score=1.0,
        content="Restart Outlook.",
    )

    service, _, _ = _service(
        [
            duplicate,
            duplicate,
        ]
    )

    result = service.ask(
        "Outlook is not syncing."
    )

    assert len(result.sources) == 1


def test_query_is_trimmed() -> None:
    service, _, retrieval = _service(
        [
            _result(
                chunk_id=(
                    "550e8400-e29b-41d4-a716-446655440006"
                ),
                score=1.0,
                content="Restart Outlook.",
            ),
            _result(
                chunk_id=(
                    "550e8400-e29b-41d4-a716-446655440007"
                ),
                score=0.9,
                content="Check connection status.",
                chunk_index=1,
            ),
        ]
    )

    result = service.ask(
        "  Outlook synchronization?  "
    )

    assert result.query == (
        "Outlook synchronization?"
    )

    assert retrieval.queries == [
        "Outlook synchronization?"
    ]


def test_empty_query_is_rejected() -> None:
    service, _, _ = _service([])

    try:
        service.ask("   ")
    except ValueError as exc:
        assert str(exc) == (
            "query cannot be empty"
        )
    else:
        raise AssertionError(
            "Expected ValueError"
        )