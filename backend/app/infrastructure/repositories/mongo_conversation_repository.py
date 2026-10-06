from pymongo.database import Database

from app.application.ports.conversation_repository import ConversationRepository
from app.domain.conversation import Conversation


class MongoConversationRepository(ConversationRepository):
    COLLECTION_NAME = "conversations"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]

    def save(self, conversation: Conversation) -> Conversation:
        document = conversation.model_dump(mode="json")

        self._collection.replace_one(
            {"conversation_id": conversation.conversation_id},
            document,
            upsert=True,
        )

        return conversation

    def get_by_id(
        self,
        conversation_id: str,
    ) -> Conversation | None:
        document = self._collection.find_one(
            {"conversation_id": conversation_id}
        )

        if document is None:
            return None

        document.pop("_id", None)

        return Conversation.model_validate(document)