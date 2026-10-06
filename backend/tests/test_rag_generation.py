from __future__ import annotations

from uuid import UUID

import pytest

from app.application.knowledge.rag_generation import (
    RAGAnswer,
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
        response: str = "Restart the VPN client.",
    ) -> None:
        self.response = response
        self.prompts: list[str] = []

    def generate(
        self,
        prompt: str,
    ) -> str:
        self.prompts.append(prompt)
        return self.response


def _metadata(
    title: str = "VPN Troubleshooting",
) -> KnowledgeMetadata:
    return KnowledgeMetadata(
        document_id=str(DOCUMENT_ID),
        title=title,
        source_type="markdown",
        category="Network",
        subcategory="VPN",
        version="1",
        language="en",
        access_level="internal",
        tags=["vpn", "network"],
    )


def _result(
    *,
    chunk_id: UUID,
    content: str,
    score: float,
    chunk_index: int = 0,
    title: str = "VPN Troubleshooting",
    retrieval_method: str = "hybrid",
) -> KnowledgeSearchResult:
    chunk = KnowledgeChunk(
        id=chunk_id,
        document_id=DOCUMENT_ID,
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


def _context():
    from app.application.knowledge.context_assembly_service import (
        RAGContextAssemblyService,
    )

    results = [
        _result(
            chunk_id=UUID(
                "550e8400-e29b-41d4-a716-446655440001"
            ),
            content="Restart the VPN client.",
            score=1.0,
        ),
        _result(
            chunk_id=UUID(
                "550e8400-e29b-41d4-a716-446655440002"
            ),
            content="Verify your corporate credentials.",
            score=0.8,
            chunk_index=1,
        ),
    ]

    assembler = RAGContextAssemblyService()

    return assembler.assemble(
        query="VPN authentication failure",
        results=results,
    )


def test_generation_returns_rag_answer() -> None:
    provider = FakeLLMProvider(
        response="Restart the VPN client."
    )

    service = RAGGenerationService(
        llm_provider=provider,
    )

    context = _context()

    result = service.generate(context)

    assert isinstance(result, RAGAnswer)
    assert result.answer == "Restart the VPN client."
    assert result.context is context


def test_generation_sends_user_question_to_llm() -> None:
    provider = FakeLLMProvider()

    service = RAGGenerationService(
        llm_provider=provider,
    )

    context = _context()

    service.generate(context)

    assert len(provider.prompts) == 1

    prompt = provider.prompts[0]

    assert "VPN authentication failure" in prompt


def test_generation_sends_knowledge_context_to_llm() -> None:
    provider = FakeLLMProvider()

    service = RAGGenerationService(
        llm_provider=provider,
    )

    context = _context()

    service.generate(context)

    prompt = provider.prompts[0]

    assert "Restart the VPN client." in prompt
    assert "Verify your corporate credentials." in prompt
    assert "VPN Troubleshooting" in prompt


def test_generation_preserves_sources() -> None:
    provider = FakeLLMProvider()

    service = RAGGenerationService(
        llm_provider=provider,
    )

    context = _context()

    result = service.generate(context)

    assert result.context is context

    assert len(result.context.sources) == 2

    assert (
        result.context.sources[0].title
        == "VPN Troubleshooting"
    )

    assert (
        result.context.sources[0].retrieval_method
        == "hybrid"
    )


def test_empty_llm_response_is_rejected() -> None:
    provider = FakeLLMProvider(
        response="   ",
    )

    service = RAGGenerationService(
        llm_provider=provider,
    )

    context = _context()

    with pytest.raises(
        ValueError,
        match="LLM response cannot be empty",
    ):
        service.generate(context)


def test_empty_query_is_rejected() -> None:
    provider = FakeLLMProvider()

    service = RAGGenerationService(
        llm_provider=provider,
    )

    from app.application.knowledge.context_assembly_service import (
        RAGContextAssemblyService,
    )

    assembler = RAGContextAssemblyService()

    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        assembler.assemble(
            query="   ",
            results=[],
        )