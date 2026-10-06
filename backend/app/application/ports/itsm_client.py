from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.itsm import ITSMRecord
from app.domain.ticket import Ticket
from app.domain.enums import TicketStatus


class ITSMClient(ABC):
    """
    Application port for external ITSM integration.

    The application layer depends on this abstraction instead of directly
    depending on ServiceNow.

    Current implementation:

        MockServiceNowClient

    Future implementation:

        ServiceNowClient
    """

    @abstractmethod
    def create_incident(
        self,
        ticket: Ticket,
    ) -> ITSMRecord:
        """
        Create an incident in the external ITSM platform.
        """
        raise NotImplementedError

    @abstractmethod
    def create_service_request(
        self,
        ticket: Ticket,
    ) -> ITSMRecord:
        """
        Create a service request in the external ITSM platform.
        """
        raise NotImplementedError

    @abstractmethod
    def get_ticket(
        self,
        external_id: str,
    ) -> ITSMRecord | None:
        """
        Retrieve an external ITSM record by external identifier.
        """
        raise NotImplementedError

    @abstractmethod
    def update_ticket(
        self,
        external_id: str,
        *,
        status: TicketStatus | None = None,
        description: str | None = None,
    ) -> ITSMRecord:
        """
        Update an existing external ITSM record.
        """
        raise NotImplementedError