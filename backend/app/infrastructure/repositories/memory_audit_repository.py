from app.application.ports.audit_repository import AuditRepository
from app.domain.audit import AuditEvent


class InMemoryAuditRepository(AuditRepository):
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def save(self, event: AuditEvent) -> AuditEvent:
        self._events.append(event)
        return event

    def get_all(self) -> list[AuditEvent]:
        return list(self._events)