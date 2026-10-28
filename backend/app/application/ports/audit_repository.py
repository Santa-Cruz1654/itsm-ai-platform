from abc import ABC, abstractmethod

from app.domain.audit import AuditEvent


class AuditRepository(ABC):
    """Port for persisting and retrieving audit events."""

    @abstractmethod
    def save(self, event: AuditEvent) -> AuditEvent:
        """Persist an audit event and return it."""
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[AuditEvent]:
        """Retrieve all persisted audit events."""
        raise NotImplementedError