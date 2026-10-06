from abc import ABC, abstractmethod

from app.domain.audit import AuditEvent


class AuditRepository(ABC):
    @abstractmethod
    def save(self, event: AuditEvent) -> AuditEvent:
        raise NotImplementedError