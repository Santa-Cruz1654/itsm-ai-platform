from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.application.knowledge.context_assembly_service import (
    RAGContextAssemblyService,
)
from app.application.knowledge.rag_generation import (
    RAGGenerationService,
)
from app.application.knowledge.retrieval_service import (
    KnowledgeRetrievalService,
)
from app.domain.knowledge import KnowledgeSearchResult


GroundingConfidence = Literal["high", "medium", "low"]


NO_GROUNDED_ANSWER = (
    "The available enterprise knowledge base does not contain "
    "enough information to answer this question."
)


@dataclass(frozen=True)
class KnowledgeAnswerSource:
    """
    One knowledge source used by the grounded answer.
    """

    document_id: str
    chunk_id: str
    chunk_index: int
    title: str
    score: float
    retrieval_method: str


@dataclass(frozen=True)
class KnowledgeAnswer:
    """
    Employee-facing result of the complete RAG workflow.

    The confidence value is an application-level grounding
    classification. It is NOT an LLM probability.
    """

    query: str
    answer: str
    grounded: bool
    confidence: GroundingConfidence
    sources: tuple[KnowledgeAnswerSource, ...]


class KnowledgeAnswerService:
    """
    Complete employee-facing knowledge workflow.

    Flow:

        query
          |
          v
        hybrid retrieval
          |
          v
        deterministic grounding gate
          |
          v
        bounded RAG context
          |
          v
        grounded LLM generation
          |
          v
        answer + sources + confidence

    Safety boundary:

        Weak retrieval evidence must never be sent
        to the LLM as if it were trusted grounding.

    The grounding threshold is an application heuristic.
    Qdrant hybrid/RRF scores are not probabilities.
    The threshold should eventually be calibrated against
    a labeled retrieval evaluation dataset.
    """

    DEFAULT_LIMIT = 5

    # Immediate application-level grounding gate.
    #
    # Current project behavior:
    #
    #   Outlook mandatory scenario:
    #       top score ~= 0.70 -> accepted
    #
    #   Weak retrieval unit test:
    #       score = 0.40 -> rejected
    #
    # This is NOT a probability.
    DEFAULT_MIN_GROUNDING_SCORE = 0.50

    # Number of chunks allowed into grounded context.
    DEFAULT_GROUNDING_RESULT_LIMIT = 5

    def __init__(
        self,
        *,
        retrieval_service: KnowledgeRetrievalService,
        context_assembly_service: RAGContextAssemblyService,
        generation_service: RAGGenerationService,
        min_grounding_score: float = DEFAULT_MIN_GROUNDING_SCORE,
        grounding_result_limit: int = DEFAULT_GROUNDING_RESULT_LIMIT,
    ) -> None:
        if min_grounding_score < 0:
            raise ValueError(
                "min_grounding_score must be greater than or equal to zero"
            )

        if grounding_result_limit < 1:
            raise ValueError(
                "grounding_result_limit must be greater than zero"
            )

        self._retrieval_service = retrieval_service
        self._context_assembly_service = context_assembly_service
        self._generation_service = generation_service
        self._min_grounding_score = min_grounding_score
        self._grounding_result_limit = grounding_result_limit

    def ask(
        self,
        query: str,
        *,
        limit: int = DEFAULT_LIMIT,
        filters: dict[str, str] | None = None,
    ) -> KnowledgeAnswer:
        """
        Execute the complete knowledge-answer workflow.
        """

        normalized_query = self._validate_query(query)

        results = self._retrieval_service.hybrid_search(
            normalized_query,
            limit=limit,
            filters=filters,
        )

        grounded_results = self._select_grounded_results(
            results
        )

        # Never invoke the LLM when retrieval does not provide
        # sufficiently strong grounding evidence.
        if not grounded_results:
            return KnowledgeAnswer(
                query=normalized_query,
                answer=NO_GROUNDED_ANSWER,
                grounded=False,
                confidence="low",
                sources=(),
            )

        context = self._context_assembly_service.assemble(
            normalized_query,
            grounded_results,
        )

        # Context assembly is another deterministic safety boundary.
        if not context.sources:
            return KnowledgeAnswer(
                query=normalized_query,
                answer=NO_GROUNDED_ANSWER,
                grounded=False,
                confidence="low",
                sources=(),
            )

        generated = self._generation_service.generate(
            context
        )

        sources = tuple(
            KnowledgeAnswerSource(
                document_id=source.document_id,
                chunk_id=source.chunk_id,
                chunk_index=source.chunk_index,
                title=source.title,
                score=source.score,
                retrieval_method=source.retrieval_method,
            )
            for source in generated.context.sources
        )

        confidence = self._confidence_for(
            grounded_results=grounded_results,
            source_count=len(sources),
        )

        return KnowledgeAnswer(
            query=normalized_query,
            answer=generated.answer,
            grounded=True,
            confidence=confidence,
            sources=sources,
        )

    def _select_grounded_results(
        self,
        results: list[KnowledgeSearchResult],
    ) -> list[KnowledgeSearchResult]:
        """
        Apply the deterministic grounding gate.

        A retrieved result is eligible for grounded generation only
        when its retrieval score meets the configured minimum.

        Duplicate chunks are removed.

        The number of accepted chunks is bounded before context
        assembly.

        Important:

        The score is treated as an application-level retrieval
        heuristic, NOT as a probability or LLM confidence score.
        """

        if not results:
            return []

        selected: list[KnowledgeSearchResult] = []
        seen_chunks: set[str] = set()

        for result in results:
            chunk_id = str(result.chunk.id)

            if chunk_id in seen_chunks:
                continue

            seen_chunks.add(chunk_id)

            if result.score < self._min_grounding_score:
                continue

            selected.append(result)

            if len(selected) >= self._grounding_result_limit:
                break

        return selected

    @staticmethod
    def _confidence_for(
        *,
        grounded_results: list[KnowledgeSearchResult],
        source_count: int,
    ) -> GroundingConfidence:
        """
        Convert grounding evidence into a simple UI classification.

        high:
            Multiple sufficiently strong retrieved chunks.

        medium:
            One sufficiently strong retrieved chunk.

        low:
            No sufficiently strong grounding evidence.

        This is not a probability.
        """

        if not grounded_results or source_count == 0:
            return "low"

        if len(grounded_results) >= 2:
            return "high"

        return "medium"

    @staticmethod
    def _validate_query(
        query: str,
    ) -> str:
        """
        Validate and normalize the employee query.
        """

        if not isinstance(query, str):
            raise ValueError(
                "query must be a string"
            )

        normalized = query.strip()

        if not normalized:
            raise ValueError(
                "query cannot be empty"
            )

        return normalized