from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from app.application.ports.embedding_provider import (
    EmbeddingProvider,
)
from app.domain.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
    deterministic_chunk_id,
)


@dataclass
class _Block:
    text: str
    heading_path: list[str]


class SemanticChunker:

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        *,
        similarity_threshold: float = 0.55,
        max_characters: int = 5000,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._similarity_threshold = similarity_threshold
        self._max_characters = max_characters

    def chunk(
        self,
        document: KnowledgeDocument,
    ) -> list[KnowledgeChunk]:

        blocks = self._extract_blocks(
            document.content
        )

        if not blocks:
            return []

        texts = [
            block.text
            for block in blocks
        ]

        embeddings = np.asarray(
            self._embedding_provider.embed_documents(
                texts
            ),
            dtype=np.float32,
        )

        chunks: list[_Block] = []

        current_text: list[str] = []
        current_heading: list[str] = []

        for index, block in enumerate(blocks):

            if not current_text:
                current_text = [block.text]
                current_heading = block.heading_path
                continue

            similarity = self._cosine_similarity(
                embeddings[index - 1],
                embeddings[index],
            )

            candidate = "\n\n".join(
                [
                    *current_text,
                    block.text,
                ]
            )

            if (
                similarity < self._similarity_threshold
                or len(candidate) > self._max_characters
            ):
                chunks.append(
                    _Block(
                        text="\n\n".join(
                            current_text
                        ),
                        heading_path=current_heading,
                    )
                )

                current_text = [block.text]
                current_heading = block.heading_path

            else:
                current_text.append(
                    block.text
                )

        if current_text:
            chunks.append(
                _Block(
                    text="\n\n".join(
                        current_text
                    ),
                    heading_path=current_heading,
                )
            )

        return [
            KnowledgeChunk(
                id=deterministic_chunk_id(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk.text,
                ),
                document_id=document.id,
                content=chunk.text,
                chunk_index=index,
                heading_path=chunk.heading_path,
                metadata=document.metadata,
            )
            for index, chunk in enumerate(chunks)
        ]

    @staticmethod
    def _cosine_similarity(
        left: np.ndarray,
        right: np.ndarray,
    ) -> float:

        left_norm = np.linalg.norm(left)
        right_norm = np.linalg.norm(right)

        if left_norm == 0 or right_norm == 0:
            return 0.0

        return float(
            np.dot(left, right)
            / (left_norm * right_norm)
        )

    @staticmethod
    def _extract_blocks(
        content: str,
    ) -> list[_Block]:

        heading_stack: list[
            tuple[int, str]
        ] = []

        blocks: list[_Block] = []
        paragraphs: list[str] = []

        def flush() -> None:

            if not paragraphs:
                return

            text = "\n".join(
                paragraphs
            ).strip()

            if text:
                blocks.append(
                    _Block(
                        text=text,
                        heading_path=[
                            title
                            for _, title
                            in heading_stack
                        ],
                    )
                )

            paragraphs.clear()

        for line in content.splitlines():

            heading_match = re.match(
                r"^(#{1,6})\s+(.+?)\s*$",
                line,
            )

            if heading_match:

                flush()

                level = len(
                    heading_match.group(1)
                )

                title = (
                    heading_match
                    .group(2)
                    .strip()
                )

                while (
                    heading_stack
                    and heading_stack[-1][0] >= level
                ):
                    heading_stack.pop()

                heading_stack.append(
                    (level, title)
                )

                continue

            if not line.strip():
                flush()
                continue

            paragraphs.append(line)

        flush()

        return blocks