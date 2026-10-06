from abc import ABC, abstractmethod

from app.domain.conversation import Conversation


class ConversationRepository(ABC):
    @abstractmethod
    def save(self, conversation: Conversation) -> Conversation:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, conversation_id: str) -> Conversation | None:
        raise NotImplementedError