from datetime import datetime, timezone

import pytest

from app.application.conversation_service import ConversationService
from app.domain.conversation import Conversation, Message
from app.domain.enums import (
    ConversationStatus,
    MessageRole,
    ResolutionType,
)
from app.infrastructure.repositories.memory_conversation_repository import (
    InMemoryConversationRepository,
)


def create_conversation() -> Conversation:
    now = datetime.now(timezone.utc)

    return Conversation(
        conversation_id="CONV-001",
        user_id="USR-001",
        status=ConversationStatus.ACTIVE,
        messages=[
            Message(
                message_id="MSG-001",
                role=MessageRole.EMPLOYEE,
                content="My VPN is not connecting.",
                created_at=now,
            ),
            Message(
                message_id="MSG-002",
                role=MessageRole.AI,
                content="Please reconnect using the approved VPN procedure.",
                created_at=now,
            ),
        ],
        created_at=now,
        updated_at=now,
    )


def create_service() -> tuple[
    ConversationService,
    InMemoryConversationRepository,
]:
    repository = InMemoryConversationRepository()
    service = ConversationService(repository)

    return service, repository


def test_resolve_self_service() -> None:
    service, repository = create_service()
    conversation = create_conversation()

    repository.save(conversation)

    result = service.resolve_self_service(
        conversation_id="CONV-001",
        summary="Employee confirmed that the VPN connection was restored.",
    )

    assert result.status == ConversationStatus.RESOLVED
    assert result.resolution is not None
    assert result.resolution.type == ResolutionType.SELF_SERVICE
    assert result.resolution.summary == (
        "Employee confirmed that the VPN connection was restored."
    )


def test_cannot_resolve_already_resolved_conversation() -> None:
    service, repository = create_service()
    conversation = create_conversation()

    conversation.status = ConversationStatus.RESOLVED
    repository.save(conversation)

    with pytest.raises(ValueError, match="already resolved"):
        service.resolve_self_service(
            conversation_id="CONV-001",
            summary="VPN was fixed.",
        )


def test_cannot_self_service_resolve_escalated_conversation() -> None:
    service, repository = create_service()
    conversation = create_conversation()

    conversation.status = ConversationStatus.ESCALATED
    repository.save(conversation)

    with pytest.raises(
        ValueError,
        match="cannot be self-service resolved",
    ):
        service.resolve_self_service(
            conversation_id="CONV-001",
            summary="VPN was fixed.",
        )


def test_resolution_summary_cannot_be_empty() -> None:
    service, repository = create_service()
    conversation = create_conversation()

    repository.save(conversation)

    with pytest.raises(ValueError, match="cannot be empty"):
        service.resolve_self_service(
            conversation_id="CONV-001",
            summary="   ",
        )