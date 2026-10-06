from uuid import UUID

import pytest

from app.domain.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeMetadata,
)


def create_metadata() -> KnowledgeMetadata:
    return KnowledgeMetadata(
        category="network",
        subcategory="vpn",
        title="VPN Troubleshooting",
        document_id="vpn-troubleshooting",
        tags=["vpn", "network", "remote-access"],
    )


def test_knowledge_metadata_is_created() -> None:
    metadata = create_metadata()

    assert metadata.category == "network"
    assert metadata.subcategory == "vpn"
    assert metadata.title == "VPN Troubleshooting"
    assert "vpn" in metadata.tags


def test_knowledge_metadata_rejects_empty_title() -> None:
    with pytest.raises(ValueError, match="metadata value cannot be empty"):
        KnowledgeMetadata(
            category="network",
            title="   ",
            document_id="vpn-troubleshooting",
        )


def test_knowledge_document_is_created() -> None:
    document = KnowledgeDocument(
        content="Employees can connect to the VPN using the corporate VPN client.",
        metadata=create_metadata(),
    )

    assert isinstance(document.id, UUID)
    assert document.content.startswith("Employees")


def test_knowledge_document_rejects_empty_content() -> None:
    with pytest.raises(
        ValueError,
        match="knowledge document content cannot be empty",
    ):
        KnowledgeDocument(
            content="   ",
            metadata=create_metadata(),
        )


def test_knowledge_chunk_is_created() -> None:
    document = KnowledgeDocument(
        content="VPN troubleshooting information.",
        metadata=create_metadata(),
    )

    chunk = KnowledgeChunk(
        document_id=document.id,
        content="Restart the VPN client and reconnect.",
        chunk_index=0,
        heading_path=["VPN Troubleshooting", "Connection Problems"],
        metadata=create_metadata(),
    )

    assert chunk.document_id == document.id
    assert chunk.chunk_index == 0
    assert chunk.heading_path == [
        "VPN Troubleshooting",
        "Connection Problems",
    ]


def test_knowledge_chunk_rejects_negative_index() -> None:
    document = KnowledgeDocument(
        content="VPN troubleshooting information.",
        metadata=create_metadata(),
    )

    with pytest.raises(ValueError):
        KnowledgeChunk(
            document_id=document.id,
            content="Restart the VPN client.",
            chunk_index=-1,
            metadata=create_metadata(),
        )