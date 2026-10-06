from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.domain.knowledge import KnowledgeSearchResult


@dataclass(frozen=True)
class RAGContextSource:
    """
    Identifies one knowledge chunk used in the final RAG context.
    """

    document_id: str
    chunk_id: str
    chunk_index: int
    title: str
    score: float
    retrieval_method: str
    

@dataclass(frozen=True)
class RAGContext:
    """
    Immutable context passed from retrieval into generation.

    This object deliberately contains both:
        1. formatted context text for the LLM
        2. structured source information for citations/evaluation
    """

    query: str
    context_text: str
    sources: tuple[RAGContextSource, ...]


class RAGContextAssemblyService:
    """
    Converts retrieval results into bounded, LLM-ready context.

    Responsibilities:
        - validate the query
        - remove duplicate chunks
        - preserve retrieval ordering
        - limit the number of chunks
        - limit context size
        - build source metadata
        - format context deterministically

    This service does NOT:
        - perform retrieval
        - call Qdrant
        - generate embeddings
        - call an LLM
        - generate the final answer
    """

    def __init__(
        self,
        *,
        max_chunks: int = 5,
        max_context_characters: int = 12000,
    ) -> None:
        if max_chunks <= 0:
            raise ValueError(
                "max_chunks must be greater than zero"
            )

        if max_context_characters <= 0:
            raise ValueError(
                "max_context_characters must be greater than zero"
            )

        self._max_chunks = max_chunks
        self._max_context_characters = max_context_characters

    def assemble(
        self,
        query: str,
        results: Iterable[KnowledgeSearchResult],
    ) -> RAGContext:
        """
        Build a deterministic RAG context from retrieval results.
        """

        query = query.strip()

        if not query:
            raise ValueError(
                "query cannot be empty"
            )

        selected_results = self._select_results(results)

        context_parts: list[str] = []
        sources: list[RAGContextSource] = []

        current_length = 0

        for result in selected_results:
            chunk = result.chunk

            block = self._format_chunk(
                result=result,
                source_number=len(sources) + 1,
            )

            block_length = len(block)

            if (
                current_length + block_length
                > self._max_context_characters
            ):
                break

            context_parts.append(block)
            current_length += block_length

            sources.append(
                RAGContextSource(
                    document_id=str(
                        chunk.metadata.document_id
                    ),
                    chunk_id=str(chunk.id),
                    chunk_index=chunk.chunk_index,
                    title=chunk.metadata.title,
                    score=float(result.score),
                    retrieval_method=(
                        result.retrieval_method
                    ),
                )
            )

        return RAGContext(
            query=query,
            context_text="\n\n".join(context_parts),
            sources=tuple(sources),
        )

    def _select_results(
        self,
        results: Iterable[KnowledgeSearchResult],
    ) -> list[KnowledgeSearchResult]:
        """
        Select unique retrieval results while preserving ranking.
        """

        selected: list[KnowledgeSearchResult] = []
        seen_chunk_ids: set[str] = set()

        for result in results:
            chunk_id = str(result.chunk.id)

            if chunk_id in seen_chunk_ids:
                continue

            seen_chunk_ids.add(chunk_id)
            selected.append(result)

            if len(selected) >= self._max_chunks:
                break

        return selected

    @staticmethod
    def _format_chunk(
        *,
        result: KnowledgeSearchResult,
        source_number: int,
    ) -> str:
        """
        Convert one retrieved chunk into a deterministic context block.
        """

        chunk = result.chunk
        metadata = chunk.metadata

        heading = ""

        if chunk.heading_path:
            heading = (
                " > ".join(chunk.heading_path)
            )

        lines = [
            f"[Source {source_number}]",
            f"Title: {metadata.title}",
            f"Document: {metadata.document_id}",
            f"Chunk: {chunk.chunk_index}",
            f"Retrieval score: {float(result.score):.6f}",
        ]

        if heading:
            lines.append(
                f"Section: {heading}"
            )

        lines.extend(
            [
                "",
                chunk.content.strip(),
            ]
        )

        return "\n".join(lines)
