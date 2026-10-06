from app.application.ports.conversation_repository import ConversationRepository
from app.domain.conversation import Conversation


class InMemoryConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}

    def save(self, conversation: Conversation) -> Conversation:
        self._conversations[conversation.conversation_id] = conversation
        return conversation

    def get_by_id(self, conversation_id: str) -> Conversation | None:
        return self._conversations.get(conversation_id)