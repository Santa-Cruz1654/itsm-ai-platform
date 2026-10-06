from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4, uuid5

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# ---------------------------------------------------------------------------
# Stable namespace
# ---------------------------------------------------------------------------
#
# UUID5 gives us deterministic UUIDs:
#
#   same logical identity -> same UUID
#   different logical identity -> different UUID
#
# This namespace is private to the ITSM knowledge subsystem.
#
KNOWLEDGE_NAMESPACE = UUID(
    "8b9c2c7e-7f4a-4c4a-9e4e-6a0f2e9d8c31"
)


# ---------------------------------------------------------------------------
# Deterministic document identity
# ---------------------------------------------------------------------------


def deterministic_document_id(
    document_id: str,
) -> UUID:
    """
    Generate the stable UUID for a logical knowledge document.

    Document identity is based on the logical document identifier,
    not the document content.

    Therefore:

        vpn-troubleshooting
            -> always produces the same UUID

    If the document content changes, the document identity does not
    change. This is important for idempotent ingestion.
    """

    normalized_document_id = document_id.strip()

    if not normalized_document_id:
        raise ValueError(
            "document_id cannot be empty"
        )

    identity = (
        "document:"
        "markdown:"
        f"{normalized_document_id}"
    )

    return uuid5(
        KNOWLEDGE_NAMESPACE,
        identity,
    )


# ---------------------------------------------------------------------------
# Deterministic chunk identity
# ---------------------------------------------------------------------------


def deterministic_chunk_id(
    *,
    document_id: UUID,
    chunk_index: int,
    content: str | None = None,
) -> UUID:
    """
    Generate the stable UUID for a knowledge chunk.

    Chunk identity is intentionally based on:

        document_id + chunk_index

    Content is accepted as an argument because the public helper is
    also used by the test contract and future callers may provide it.

    Content is deliberately NOT part of the identity.

    This means:

        same document + same chunk index
            -> same chunk UUID

    even when the chunk content changes.

    That is required for idempotent ingestion because an updated chunk
    should overwrite the existing vector rather than create a new one.
    """

    if chunk_index < 0:
        raise ValueError(
            "chunk_index must be greater than or equal to zero"
        )

    # The content parameter is intentionally unused.
    #
    # Do not include content in the UUID calculation.
    #
    # If content were included:
    #
    #     old content -> UUID A
    #     new content -> UUID B
    #
    # and ingestion would create a new point instead of updating the
    # existing logical chunk.
    _ = content

    identity = (
        "chunk:"
        f"{document_id}:"
        f"{chunk_index}"
    )

    return uuid5(
        KNOWLEDGE_NAMESPACE,
        identity,
    )


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class KnowledgeMetadata(BaseModel):
    """
    Metadata attached to a knowledge document and its chunks.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    source_type: str = "markdown"

    category: str

    subcategory: str | None = None

    title: str

    document_id: str

    version: str = "1"

    language: str = "en"

    access_level: str = "internal"

    tags: list[str] = Field(
        default_factory=list
    )

    @field_validator(
        "source_type",
        "category",
        "title",
        "document_id",
        "version",
        "language",
        "access_level",
    )
    @classmethod
    def validate_non_empty(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "metadata value cannot be empty"
            )

        return value

    @field_validator("subcategory")
    @classmethod
    def normalize_subcategory(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


# ---------------------------------------------------------------------------
# Knowledge document
# ---------------------------------------------------------------------------


class KnowledgeDocument(BaseModel):
    """
    Logical knowledge document.

    The document ID is deterministic when the caller does not explicitly
    provide an ID.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    id: UUID = Field(
        default_factory=uuid4
    )

    content: str

    metadata: KnowledgeMetadata

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    @model_validator(mode="before")
    @classmethod
    def assign_deterministic_id(
        cls,
        data: Any,
    ) -> Any:
        """
        Automatically assign the deterministic document ID when the
        caller does not explicitly provide one.

        This is deliberately a `before` validator so that Pydantic can
        still treat `id` as a normal UUID field.
        """

        if not isinstance(data, dict):
            return data

        if data.get("id") is not None:
            return data

        metadata = data.get("metadata")

        if isinstance(
            metadata,
            KnowledgeMetadata,
        ):
            logical_document_id = (
                metadata.document_id
            )

        elif isinstance(
            metadata,
            dict,
        ):
            logical_document_id = metadata.get(
                "document_id"
            )

        else:
            return data

        if not logical_document_id:
            return data

        updated = dict(data)

        updated["id"] = (
            deterministic_document_id(
                str(logical_document_id)
            )
        )

        return updated

    @field_validator("content")
    @classmethod
    def validate_content(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "knowledge document content cannot be empty"
            )

        return value

    @classmethod
    def deterministic_id(
        cls,
        metadata: KnowledgeMetadata,
    ) -> UUID:
        """
        Compatibility helper for callers that want to explicitly
        generate the deterministic document identity.
        """

        return deterministic_document_id(
            metadata.document_id
        )

    @classmethod
    def from_metadata(
        cls,
        *,
        content: str,
        metadata: KnowledgeMetadata,
    ) -> KnowledgeDocument:
        """
        Construct a knowledge document using its deterministic identity.
        """

        return cls(
            id=deterministic_document_id(
                metadata.document_id
            ),
            content=content,
            metadata=metadata,
        )


# ---------------------------------------------------------------------------
# Knowledge chunk
# ---------------------------------------------------------------------------


class KnowledgeChunk(BaseModel):
    """
    A retrievable chunk belonging to a knowledge document.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    id: UUID = Field(
        default_factory=uuid4
    )

    document_id: UUID

    content: str

    chunk_index: int = Field(
        ge=0
    )

    heading_path: list[str] = Field(
        default_factory=list
    )

    metadata: KnowledgeMetadata

    @model_validator(mode="before")
    @classmethod
    def assign_deterministic_id(
        cls,
        data: Any,
    ) -> Any:
        """
        Automatically assign a deterministic chunk ID when the caller
        does not explicitly provide one.
        """

        if not isinstance(data, dict):
            return data

        if data.get("id") is not None:
            return data

        document_id = data.get(
            "document_id"
        )

        chunk_index = data.get(
            "chunk_index"
        )

        if (
            document_id is None
            or chunk_index is None
        ):
            return data

        updated = dict(data)

        updated["id"] = deterministic_chunk_id(
            document_id=UUID(
                str(document_id)
            ),
            chunk_index=int(
                chunk_index
            ),
            content=data.get(
                "content"
            ),
        )

        return updated

    @field_validator("content")
    @classmethod
    def validate_content(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "knowledge chunk content cannot be empty"
            )

        return value

    @classmethod
    def deterministic_id(
        cls,
        *,
        document_id: UUID,
        chunk_index: int,
        content: str | None = None,
    ) -> UUID:
        """
        Compatibility helper for explicit deterministic chunk creation.
        """

        return deterministic_chunk_id(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
        )

    @classmethod
    def from_document(
        cls,
        *,
        document: KnowledgeDocument,
        content: str,
        chunk_index: int,
        heading_path: list[str],
    ) -> KnowledgeChunk:
        """
        Construct a deterministic chunk from a document.
        """

        return cls(
            id=deterministic_chunk_id(
                document_id=document.id,
                chunk_index=chunk_index,
                content=content,
            ),
            document_id=document.id,
            content=content,
            chunk_index=chunk_index,
            heading_path=heading_path,
            metadata=document.metadata,
        )


# ---------------------------------------------------------------------------
# Retrieval result
# ---------------------------------------------------------------------------

class KnowledgeSearchResult(BaseModel):
    """
    Result returned by a retrieval strategy.

    The retrieval layer exposes one canonical score.

    For dense retrieval:
        score = dense similarity score

    For BM25:
        score = lexical retrieval score

    For hybrid retrieval:
        score = final fused/RRF score returned by the
        vector-store implementation.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    chunk: KnowledgeChunk

    score: float

    retrieval_method: str = "dense"

    @property
    def hybrid_score(self) -> float:
        """
        Backward-compatible alias for consumers that still refer
        to the final hybrid retrieval score by its historical name.
        """
        return self.score

# ---------------------------------------------------------------------------
# Hybrid retrieval result
# ---------------------------------------------------------------------------


class KnowledgeHybridSearchResult(BaseModel):
    """
    Result produced when dense and keyword retrieval are combined.

    This model is intentionally retained because the current retrieval
    service already exposes a hybrid-search path.

    It does NOT mean that the production BM25/RRF implementation is
    finished. That is a later retrieval milestone.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    chunk: KnowledgeChunk

    dense_score: float

    keyword_score: float

    hybrid_score: float