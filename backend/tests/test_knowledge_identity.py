from uuid import UUID

from app.domain.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeMetadata,
    deterministic_chunk_id,
    deterministic_document_id,
)


def create_metadata() -> KnowledgeMetadata:
    return KnowledgeMetadata(
        category="network",
        subcategory="vpn",
        title="VPN Troubleshooting",
        document_id="vpn-troubleshooting",
        tags=[
            "vpn",
            "network",
            "remote-access",
        ],
    )


def test_document_id_is_deterministic() -> None:

    metadata = create_metadata()

    first = KnowledgeDocument(
        content="VPN troubleshooting information.",
        metadata=metadata,
    )

    second = KnowledgeDocument(
        content="VPN troubleshooting information.",
        metadata=metadata,
    )

    assert isinstance(
        first.id,
        UUID,
    )

    assert first.id == second.id

    assert first.id == deterministic_document_id(
        "vpn-troubleshooting"
    )


def test_chunk_ids_are_deterministic() -> None:

    metadata = create_metadata()

    first_document = KnowledgeDocument(
        content="VPN troubleshooting information.",
        metadata=metadata,
    )

    second_document = KnowledgeDocument(
        content="VPN troubleshooting information.",
        metadata=metadata,
    )

    first_chunk = KnowledgeChunk(
        id=deterministic_chunk_id(
            document_id=first_document.id,
            chunk_index=0,
            content="Restart the VPN client.",
        ),
        document_id=first_document.id,
        content="Restart the VPN client.",
        chunk_index=0,
        metadata=metadata,
    )

    second_chunk = KnowledgeChunk(
        id=deterministic_chunk_id(
            document_id=second_document.id,
            chunk_index=0,
            content="Restart the VPN client.",
        ),
        document_id=second_document.id,
        content="Restart the VPN client.",
        chunk_index=0,
        metadata=metadata,
    )

    assert first_chunk.id == second_chunk.id

    assert first_chunk.id == deterministic_chunk_id(
        document_id=first_document.id,
        chunk_index=0,
        content="Restart the VPN client.",
    )


def test_chunk_ids_are_unique_within_document() -> None:

    document_id = deterministic_document_id(
        "vpn-troubleshooting"
    )

    first = deterministic_chunk_id(
        document_id=document_id,
        chunk_index=0,
        content="Restart the VPN client.",
    )

    second = deterministic_chunk_id(
        document_id=document_id,
        chunk_index=1,
        content="Restart the VPN client.",
    )

    assert first != second


def test_different_documents_have_different_ids() -> None:

    first = deterministic_document_id(
        "vpn-troubleshooting"
    )

    second = deterministic_document_id(
        "password-reset"
    )

    assert first != second


def test_same_chunk_content_with_different_index_has_different_id() -> None:

    document_id = deterministic_document_id(
        "vpn-troubleshooting"
    )

    first = deterministic_chunk_id(
        document_id=document_id,
        chunk_index=0,
        content="Restart the VPN client.",
    )

    second = deterministic_chunk_id(
        document_id=document_id,
        chunk_index=1,
        content="Restart the VPN client.",
    )

    assert first != second