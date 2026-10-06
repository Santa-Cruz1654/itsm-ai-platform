from datetime import datetime, timezone

from app.domain.audit import AuditEvent
from app.domain.conversation import Conversation, Message
from app.domain.enums import ConversationStatus, MessageRole
from app.infrastructure.database.mongodb import MongoDB
from app.infrastructure.repositories.mongo_audit_repository import (
    MongoAuditRepository,
)
from app.infrastructure.repositories.mongo_conversation_repository import (
    MongoConversationRepository,
)


MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "itsm_test"


def create_conversation() -> Conversation:
    now = datetime.now(timezone.utc)

    return Conversation(
        conversation_id="CONV-MONGO-001",
        user_id="USR-001",
        status=ConversationStatus.ACTIVE,
        messages=[
            Message(
                message_id="MSG-MONGO-001",
                role=MessageRole.EMPLOYEE,
                content="My VPN is not connecting.",
                created_at=now,
            )
        ],
        created_at=now,
        updated_at=now,
    )


def create_audit_event() -> AuditEvent:
    return AuditEvent(
        event_id="AUDIT-MONGO-001",
        event_type="conversation_created",
        user_id="USR-001",
        conversation_id="CONV-MONGO-001",
        actor="system",
        description="Conversation created.",
        metadata={"source": "test"},
        created_at=datetime.now(timezone.utc),
    )


def test_mongo_conversation_repository() -> None:
    database = MongoDB(
        uri=MONGO_URI,
        database_name=DATABASE_NAME,
    )

    try:
        repository = MongoConversationRepository(database.database)

        repository._collection.delete_many(
            {"conversation_id": "CONV-MONGO-001"}
        )

        conversation = create_conversation()

        saved = repository.save(conversation)

        assert saved.conversation_id == "CONV-MONGO-001"

        retrieved = repository.get_by_id("CONV-MONGO-001")

        assert retrieved is not None
        assert retrieved.conversation_id == conversation.conversation_id
        assert retrieved.user_id == conversation.user_id
        assert retrieved.status == conversation.status
        assert len(retrieved.messages) == 1
        assert retrieved.messages[0].content == (
            "My VPN is not connecting."
        )

    finally:
        database.close()


def test_mongo_conversation_repository_returns_none_for_missing() -> None:
    database = MongoDB(
        uri=MONGO_URI,
        database_name=DATABASE_NAME,
    )

    try:
        repository = MongoConversationRepository(database.database)

        repository._collection.delete_many(
            {"conversation_id": "CONV-MONGO-MISSING"}
        )

        result = repository.get_by_id("CONV-MONGO-MISSING")

        assert result is None

    finally:
        database.close()


def test_mongo_audit_repository() -> None:
    database = MongoDB(
        uri=MONGO_URI,
        database_name=DATABASE_NAME,
    )

    try:
        repository = MongoAuditRepository(database.database)

        repository._collection.delete_many(
            {"event_id": "AUDIT-MONGO-001"}
        )

        event = create_audit_event()

        saved = repository.save(event)

        assert saved.event_id == "AUDIT-MONGO-001"

        document = repository._collection.find_one(
            {"event_id": "AUDIT-MONGO-001"}
        )

        assert document is not None
        assert document["event_type"] == "conversation_created"
        assert document["user_id"] == "USR-001"
        assert document["conversation_id"] == "CONV-MONGO-001"
        assert document["actor"] == "system"
        assert document["metadata"]["source"] == "test"

    finally:
        database.close()