from pymongo.database import Database

from app.application.ports.audit_repository import AuditRepository
from app.domain.audit import AuditEvent


class MongoAuditRepository(AuditRepository):
    COLLECTION_NAME = "audit_events"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]

    def save(self, event: AuditEvent) -> AuditEvent:
        document = event.model_dump(mode="json")
        self._collection.insert_one(document)
        return event

    def list_all(self) -> list[AuditEvent]:
        """Retrieve persisted audit events from MongoDB."""
        events: list[AuditEvent] = []

        for document in self._collection.find():
            document.pop("_id", None)
            events.append(AuditEvent.model_validate(document))

        return events