from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from app.application.ports.itsm_client import ITSMClient
from app.domain.enums import TicketStatus, TicketType
from app.domain.itsm import ITSMRecord
from app.domain.ticket import Ticket


class MockServiceNowClient(ITSMClient):
    """
    In-memory ServiceNow-like ITSM adapter.

    This is NOT the application's database.

    It deliberately simulates the external ITSM boundary:

        create
        read
        update

    The implementation is stateful so that tests can verify complete
    create -> get -> update behavior.

    A future real ServiceNowClient can implement the same ITSMClient
    contract without changing TicketService.
    """

    EXTERNAL_SYSTEM = "mock_servicenow"

    def __init__(self) -> None:
        self._records: dict[str, ITSMRecord] = {}
        self._lock = Lock()

        self._incident_counter = 1000
        self._request_counter = 1000

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_incident(
        self,
        ticket: Ticket,
    ) -> ITSMRecord:
        """
        Simulate creation of a ServiceNow incident.
        """

        if ticket.type != TicketType.INCIDENT:
            raise ValueError(
                "create_incident requires an incident ticket."
            )

        return self._create_record(
            ticket=ticket,
            ticket_type=TicketType.INCIDENT,
        )

    def create_service_request(
        self,
        ticket: Ticket,
    ) -> ITSMRecord:
        """
        Simulate creation of a ServiceNow service request.
        """

        if ticket.type != TicketType.REQUEST:
            raise ValueError(
                "create_service_request requires a request ticket."
            )

        return self._create_record(
            ticket=ticket,
            ticket_type=TicketType.REQUEST,
        )

    def get_ticket(
        self,
        external_id: str,
    ) -> ITSMRecord | None:
        """
        Retrieve a record from the mock external ITSM system.
        """

        external_id = external_id.strip()

        if not external_id:
            raise ValueError(
                "External ticket ID cannot be empty."
            )

        with self._lock:
            record = self._records.get(external_id)

            if record is None:
                return None

            return deepcopy(record)

    def update_ticket(
        self,
        external_id: str,
        *,
        status: TicketStatus | None = None,
        description: str | None = None,
    ) -> ITSMRecord:
        """
        Update an existing mock ITSM record.
        """

        external_id = external_id.strip()

        if not external_id:
            raise ValueError(
                "External ticket ID cannot be empty."
            )

        if description is not None and not description.strip():
            raise ValueError(
                "Description cannot be empty."
            )

        with self._lock:
            existing = self._records.get(
                external_id
            )

            if existing is None:
                raise KeyError(
                    f"External ticket not found: {external_id}"
                )

            now = datetime.now(timezone.utc)

            updated = existing.model_copy(
                update={
                    "status": (
                        status.value
                        if status is not None
                        else existing.status
                    ),
                    "updated_at": now,
                }
            )

            self._records[external_id] = updated

            return deepcopy(updated)

    # ------------------------------------------------------------------
    # Test / diagnostic helpers
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """
        Remove all records from the mock external system.

        Intended primarily for tests.
        """

        with self._lock:
            self._records.clear()

    def count(self) -> int:
        """
        Return the number of external records currently stored.
        """

        with self._lock:
            return len(self._records)

    # ------------------------------------------------------------------
    # Internal record creation
    # ------------------------------------------------------------------

    def _create_record(
        self,
        *,
        ticket: Ticket,
        ticket_type: TicketType,
    ) -> ITSMRecord:
        with self._lock:
            now = datetime.now(timezone.utc)

            external_id = str(
                uuid4()
            )

            external_number = (
                self._next_incident_number()
                if ticket_type == TicketType.INCIDENT
                else self._next_request_number()
            )

            record = ITSMRecord(
                external_system=self.EXTERNAL_SYSTEM,
                external_id=external_id,
                external_number=external_number,
                ticket_type=ticket_type,
                status=TicketStatus.OPEN.value,
                created_at=now,
                updated_at=now,
            )

            self._records[external_id] = record

            return deepcopy(record)

    def _next_incident_number(self) -> str:
        number = (
            f"INC{self._incident_counter}"
        )

        self._incident_counter += 1

        return number

    def _next_request_number(self) -> str:
        number = (
            f"REQ{self._request_counter}"
        )

        self._request_counter += 1

        return number