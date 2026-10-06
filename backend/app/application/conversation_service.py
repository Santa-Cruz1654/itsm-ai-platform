from datetime import datetime, timezone

from app.application.ports.conversation_repository import ConversationRepository
from app.domain.conversation import Conversation, Resolution
from app.domain.enums import ConversationStatus, ResolutionType


class ConversationService:
    """Application use cases for managing conversations."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
    ) -> None:
        self._conversation_repository = conversation_repository

    def resolve_self_service(
        self,
        conversation_id: str,
        summary: str,
    ) -> Conversation:
        conversation = self._conversation_repository.get_by_id(
            conversation_id
        )

        if conversation is None:
            raise ValueError("Conversation not found.")

        if conversation.status == ConversationStatus.RESOLVED:
            raise ValueError("Conversation is already resolved.")

        if conversation.status == ConversationStatus.ESCALATED:
            raise ValueError(
                "Escalated conversation cannot be self-service resolved."
            )

        if not summary.strip():
            raise ValueError("Resolution summary cannot be empty.")

        now = datetime.now(timezone.utc)

        conversation.status = ConversationStatus.RESOLVED

        conversation.resolution = Resolution(
            type=ResolutionType.SELF_SERVICE,
            summary=summary,
            resolved_at=now,
        )

        conversation.updated_at = now

        return self._conversation_repository.save(conversation)