import pytest

from app.application.ticket_service import TicketService
from app.domain.enums import TicketStatus, TicketType


def create_service() -> TicketService:
    return TicketService()


def test_create_incident() -> None:
    service = create_service()

    ticket = service.create_ticket(
        ticket_type=TicketType.INCIDENT,
        title="VPN connection failure",
        description="Employee cannot connect to the corporate VPN.",
        user_id="USR-001",
    )

    assert ticket.type == TicketType.INCIDENT
    assert ticket.status == TicketStatus.OPEN
    assert ticket.title == "VPN connection failure"
    assert ticket.user_id == "USR-001"


def test_create_request() -> None:
    service = create_service()

    ticket = service.create_ticket(
        ticket_type=TicketType.REQUEST,
        title="Request additional monitor",
        description="Employee requires an additional monitor.",
        user_id="USR-002",
    )

    assert ticket.type == TicketType.REQUEST
    assert ticket.status == TicketStatus.OPEN


def test_ticket_title_cannot_be_empty() -> None:
    service = create_service()

    with pytest.raises(ValueError, match="title cannot be empty"):
        service.create_ticket(
            ticket_type=TicketType.INCIDENT,
            title="   ",
            description="VPN is unavailable.",
            user_id="USR-001",
        )


def test_ticket_description_cannot_be_empty() -> None:
    service = create_service()

    with pytest.raises(ValueError, match="description cannot be empty"):
        service.create_ticket(
            ticket_type=TicketType.INCIDENT,
            title="VPN failure",
            description="   ",
            user_id="USR-001",
        )


def test_ticket_user_id_cannot_be_empty() -> None:
    service = create_service()

    with pytest.raises(ValueError, match="User ID cannot be empty"):
        service.create_ticket(
            ticket_type=TicketType.INCIDENT,
            title="VPN failure",
            description="VPN is unavailable.",
            user_id="   ",
        )