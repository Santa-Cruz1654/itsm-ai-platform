from datetime import datetime, timezone

from app.domain.conversation import Conversation, Message, Resolution
from app.domain.enums import (
    ConversationStatus,
    MessageRole,
    ResolutionType,
)


def test_self_service_conversation_can_be_resolved_without_ticket() -> None:
    now = datetime.now(timezone.utc)

    conversation = Conversation(
        conversation_id="CONV-001",
        user_id="USR-001",
        status=ConversationStatus.RESOLVED,
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
                content="Please reconnect to the corporate VPN using the approved procedure.",
                created_at=now,
            ),
            Message(
                message_id="MSG-003",
                role=MessageRole.EMPLOYEE,
                content="That fixed it.",
                created_at=now,
            ),
        ],
        resolution=Resolution(
            type=ResolutionType.SELF_SERVICE,
            summary="VPN connection restored through approved self-service guidance.",
            resolved_at=now,
        ),
        created_at=now,
        updated_at=now,
    )

    assert conversation.status == ConversationStatus.RESOLVED
    assert conversation.resolution is not None
    assert conversation.resolution.type == ResolutionType.SELF_SERVICE
    assert len(conversation.messages) == 3