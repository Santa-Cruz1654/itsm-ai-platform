from __future__ import annotations

from app.application.ticket_service import TicketService
from app.domain.enums import (
    TicketStatus,
    TicketType,
)
from app.infrastructure.itsm.mock_servicenow_client import (
    MockServiceNowClient,
)
from app.infrastructure.repositories.memory_ticket_repository import (
    MemoryTicketRepository,
)


def create_service() -> tuple[
    TicketService,
    MemoryTicketRepository,
    MockServiceNowClient,
]:
    repository = MemoryTicketRepository()

    itsm_client = MockServiceNowClient()

    service = TicketService(
        ticket_repository=repository,
        itsm_client=itsm_client,
    )

    return (
        service,
        repository,
        itsm_client,
    )


def test_incident_is_persisted_and_synchronized() -> None:
    (
        service,
        repository,
        itsm_client,
    ) = create_service()

    ticket = service.create_ticket(
        ticket_type=TicketType.INCIDENT,
        title="VPN connection failure",
        description=(
            "Employee cannot connect to VPN."
        ),
        user_id="USR-001",
    )

    assert ticket.ticket_id.startswith(
        "TKT-"
    )

    assert ticket.status == (
        TicketStatus.OPEN
    )

    assert ticket.external_system == (
        "mock_servicenow"
    )

    assert ticket.external_ticket_id is not None

    assert ticket.external_ticket_number is not None

    assert ticket.external_ticket_number.startswith(
        "INC"
    )

    assert ticket.external_sync_status == (
        "synchronized"
    )

    stored = repository.get_by_id(
        ticket.ticket_id
    )

    assert stored is not None

    assert (
        stored.external_ticket_id
        == ticket.external_ticket_id
    )

    external = itsm_client.get_ticket(
        ticket.external_ticket_id
    )

    assert external is not None

    assert (
        external.external_number
        == ticket.external_ticket_number
    )


def test_service_request_is_persisted_and_synchronized() -> None:
    (
        service,
        repository,
        itsm_client,
    ) = create_service()

    ticket = service.create_ticket(
        ticket_type=TicketType.REQUEST,
        title="Request additional monitor",
        description=(
            "Employee requires an additional monitor."
        ),
        user_id="USR-002",
    )

    assert ticket.type == (
        TicketType.REQUEST
    )

    assert ticket.external_system == (
        "mock_servicenow"
    )

    assert ticket.external_ticket_number.startswith(
        "REQ"
    )

    assert ticket.external_sync_status == (
        "synchronized"
    )

    stored = repository.get_by_id(
        ticket.ticket_id
    )

    assert stored is not None

    external = itsm_client.get_ticket(
        ticket.external_ticket_id
    )

    assert external is not None


def test_ticket_service_can_work_without_external_client() -> None:
    repository = MemoryTicketRepository()

    service = TicketService(
        ticket_repository=repository,
        itsm_client=None,
    )

    ticket = service.create_ticket(
        ticket_type=TicketType.INCIDENT,
        title="VPN failure",
        description="VPN is unavailable.",
        user_id="USR-003",
    )

    assert ticket.external_system is None

    assert ticket.external_ticket_id is None

    assert ticket.external_ticket_number is None

    assert ticket.external_sync_status == (
        "pending"
    )


def test_external_sync_failure_does_not_lose_internal_ticket() -> None:
    class FailingITSMClient(
        MockServiceNowClient
    ):
        def create_incident(self, ticket):
            raise RuntimeError(
                "Mock ServiceNow unavailable."
            )

    repository = MemoryTicketRepository()

    service = TicketService(
        ticket_repository=repository,
        itsm_client=FailingITSMClient(),
    )

    ticket = service.create_ticket(
        ticket_type=TicketType.INCIDENT,
        title="VPN failure",
        description="VPN is unavailable.",
        user_id="USR-004",
    )

    assert ticket.ticket_id.startswith(
        "TKT-"
    )

    assert ticket.external_sync_status == (
        "failed"
    )

    assert ticket.external_sync_error == (
        "Mock ServiceNow unavailable."
    )

    stored = repository.get_by_id(
        ticket.ticket_id
    )

    assert stored is not None

    assert stored.ticket_id == (
        ticket.ticket_id
    )