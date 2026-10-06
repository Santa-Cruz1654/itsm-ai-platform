from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.domain.knowledge import KnowledgeSearchResult


@dataclass(frozen=True)
class RAGContextItem:
    """
    One retrieved knowledge item prepared for LLM context.

    This is an application-level representation.

    It deliberately does not contain:
    - Qdrant-specific objects
    - embeddings
    - provider-specific information
    """

    rank: int
    content: str
    score: float
    retrieval_method: str
    document_id: str
    chunk_index: int
    title: str
    category: str
    heading_path: tuple[str, ...]


@dataclass(frozen=True)
class RAGContext:
    """
    Final context prepared for downstream LLM generation.

    The LLM layer should consume this object without knowing
    anything about Qdrant or retrieval internals.
    """

    query: str
    items: tuple[RAGContextItem, ...]
    text: str
    character_count: int

    @property
    def is_empty(self) -> bool:
        return not self.items


class RAGContextBuilder:
    """
    Build deterministic LLM-ready context from retrieval results.

    Responsibilities:
    - validate the query
    - preserve retrieval order
    - remove duplicate chunks
    - enforce result-count limits
    - enforce a character budget
    - format the final context

    Does NOT:
    - perform retrieval
    - call Qdrant
    - generate embeddings
    - call an LLM
    - decide whether an answer is correct
    """

    def __init__(
        self,
        *,
        max_items: int = 5,
        max_characters: int = 12_000,
    ) -> None:
        if max_items <= 0:
            raise ValueError("max_items must be greater than zero")

        if max_characters <= 0:
            raise ValueError(
                "max_characters must be greater than zero"
            )

        self._max_items = max_items
        self._max_characters = max_characters

    def build(
        self,
        *,
        query: str,
        results: Iterable[KnowledgeSearchResult],
    ) -> RAGContext:
        """
        Convert retrieved knowledge results into LLM-ready context.
        """

        normalized_query = self._validate_query(query)

        unique_results = self._deduplicate(results)

        selected_items: list[RAGContextItem] = []

        current_character_count = 0

        for result in unique_results:
            if len(selected_items) >= self._max_items:
                break

            item = self._to_context_item(
                result=result,
                rank=len(selected_items) + 1,
            )

            formatted_item = self._format_item(item)

            additional_characters = len(formatted_item)

            if (
                selected_items
                and current_character_count + additional_characters
                > self._max_characters
            ):
                break

            if (
                not selected_items
                and additional_characters > self._max_characters
            ):
                item = self._truncate_item(
                    item,
                    self._max_characters,
                )

                formatted_item = self._format_item(item)
                additional_characters = len(formatted_item)

            selected_items.append(item)
            current_character_count += additional_characters

        context_text = self._format_context(
            selected_items
        )

        return RAGContext(
            query=normalized_query,
            items=tuple(selected_items),
            text=context_text,
            character_count=len(context_text),
        )

    @staticmethod
    def _validate_query(query: str) -> str:
        normalized = query.strip()

        if not normalized:
            raise ValueError("query cannot be empty")

        return normalized

    @staticmethod
    def _deduplicate(
        results: Iterable[KnowledgeSearchResult],
    ) -> list[KnowledgeSearchResult]:
        """
        Remove duplicate chunks while preserving retrieval order.

        Chunk ID is the strongest identity boundary.

        If a malformed result does not expose a usable chunk ID,
        document ID + chunk index is used as a fallback.
        """

        seen: set[str] = set()
        unique: list[KnowledgeSearchResult] = []

        for result in results:
            chunk = result.chunk

            key = str(chunk.id).strip()

            if not key:
                key = (
                    f"{chunk.document_id}:"
                    f"{chunk.chunk_index}"
                )

            if key in seen:
                continue

            seen.add(key)
            unique.append(result)

        return unique

    @staticmethod
    def _to_context_item(
        *,
        result: KnowledgeSearchResult,
        rank: int,
    ) -> RAGContextItem:
        chunk = result.chunk
        metadata = chunk.metadata

        return RAGContextItem(
            rank=rank,
            content=chunk.content.strip(),
            score=float(result.score),
            retrieval_method=str(
                result.retrieval_method
            ),
            document_id=str(chunk.document_id),
            chunk_index=int(chunk.chunk_index),
            title=str(metadata.title),
            category=str(metadata.category),
            heading_path=tuple(
                chunk.heading_path
            ),
        )

    @staticmethod
    def _format_item(
        item: RAGContextItem,
    ) -> str:
        heading = " > ".join(
            item.heading_path
        )

        source = (
            item.title
            if not heading
            else f"{item.title} > {heading}"
        )

        return (
            f"[Source {item.rank}]\n"
            f"Title: {item.title}\n"
            f"Category: {item.category}\n"
            f"Document ID: {item.document_id}\n"
            f"Chunk: {item.chunk_index}\n"
            f"Retrieval: {item.retrieval_method}\n"
            f"Score: {item.score:.6f}\n"
            f"Section: {source}\n"
            f"Content:\n"
            f"{item.content}\n"
        )

    def _format_context(
        self,
        items: list[RAGContextItem],
    ) -> str:
        if not items:
            return ""

        return "\n---\n\n".join(
            self._format_item(item).strip()
            for item in items
        )

    @staticmethod
    def _truncate_item(
        item: RAGContextItem,
        max_characters: int,
    ) -> RAGContextItem:
        """
        Truncate only the content of an oversized first result.

        Metadata is preserved.
        """

        prefix = (
            f"[Source {item.rank}]\n"
            f"Title: {item.title}\n"
            f"Category: {item.category}\n"
            f"Document ID: {item.document_id}\n"
            f"Chunk: {item.chunk_index}\n"
            f"Retrieval: {item.retrieval_method}\n"
            f"Score: {item.score:.6f}\n"
            f"Content:\n"
        )

        available = max(
            0,
            max_characters - len(prefix) - 3,
        )

        return RAGContextItem(
            rank=item.rank,
            content=item.content[:available] + "...",
            score=item.score,
            retrieval_method=item.retrieval_method,
            document_id=item.document_id,
            chunk_index=item.chunk_index,
            title=item.title,
            category=item.category,
            heading_path=item.heading_path,
        )