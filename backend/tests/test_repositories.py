from datetime import datetime, timezone

from app.domain.audit import AuditEvent
from app.domain.conversation import Conversation
from app.domain.enums import ConversationStatus
from app.infrastructure.repositories.memory_audit_repository import (
    InMemoryAuditRepository,
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
        created_at=now,
        updated_at=now,
    )


def test_conversation_repository_can_save_and_get() -> None:
    repository = InMemoryConversationRepository()
    conversation = create_conversation()

    repository.save(conversation)

    result = repository.get_by_id("CONV-001")

    assert result is not None
    assert result.conversation_id == "CONV-001"


def test_conversation_repository_returns_none_for_unknown_id() -> None:
    repository = InMemoryConversationRepository()

    assert repository.get_by_id("UNKNOWN") is None


def test_audit_repository_can_save_event() -> None:
    repository = InMemoryAuditRepository()
    now = datetime.now(timezone.utc)

    event = AuditEvent(
        event_id="EVENT-001",
        event_type="test_event",
        user_id="USR-001",
        actor="system",
        description="Test audit event.",
        created_at=now,
    )

    repository.save(event)

    events = repository.get_all()

    assert len(events) == 1
    assert events[0].event_id == "EVENT-001"