from app.application.ports.audit_repository import AuditRepository
from app.domain.audit import AuditEvent


class InMemoryAuditRepository(AuditRepository):
    """In-memory audit repository, primarily useful for testing."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def save(self, event: AuditEvent) -> AuditEvent:
        self._events.append(event)
        return event

    def list_all(self) -> list[AuditEvent]:
        """Return a copy of the stored audit events."""
        return list(self._events)

    def get_all(self) -> list[AuditEvent]:
        """Backward-compatible alias for existing callers."""
        return self.list_all()