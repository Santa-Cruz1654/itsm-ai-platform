from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Stable namespace dedicated to ITSM knowledge chunk identities.
KNOWLEDGE_CHUNK_NAMESPACE = uuid.UUID(
    "7f4d6f0d-5c9b-4b7e-9a4c-7e5c7d1f4a21"
)


def deterministic_chunk_id(
    *,
    document_id: str,
    chunk_index: int,
    content: str,
) -> UUID:
    """
    Generate a deterministic UUID for a knowledge chunk.

    The same document identity, chunk index, and normalized content
    always produce the same UUID.

    This allows repeated knowledge ingestion to upsert the same
    logical chunks instead of creating duplicate vector points.
    """

    normalized_document_id = document_id.strip()

    normalized_content = content.strip()

    if not normalized_document_id:
        raise ValueError(
            "document_id cannot be empty"
        )

    if chunk_index < 0:
        raise ValueError(
            "chunk_index cannot be negative"
        )

    if not normalized_content:
        raise ValueError(
            "content cannot be empty"
        )

    identity_material = (
        f"{normalized_document_id}:"
        f"{chunk_index}:"
        f"{normalized_content}"
    )

    return uuid.uuid5(
        KNOWLEDGE_CHUNK_NAMESPACE,
        identity_material,
    )


class KnowledgeMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str = "markdown"
    category: str
    subcategory: str | None = None
    title: str
    document_id: str
    version: str = "1"
    language: str = "en"
    access_level: str = "internal"
    tags: list[str] = Field(default_factory=list)

    @field_validator(
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


class KnowledgeDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(
        default_factory=uuid4,
    )

    content: str

    metadata: KnowledgeMetadata

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

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


class KnowledgeChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(
        default_factory=uuid4,
    )

    document_id: UUID

    content: str

    chunk_index: int = Field(
        ge=0,
    )

    heading_path: list[str] = Field(
        default_factory=list,
    )

    metadata: KnowledgeMetadata

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