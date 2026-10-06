from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.domain.enums import TicketStatus, TicketType
from app.domain.ticket import Ticket


def test_ticket_defaults_to_new_status() -> None:
    now = datetime.now(timezone.utc)

    ticket = Ticket(
        ticket_id="INC-001",
        user_id="USR-001",
        type=TicketType.INCIDENT,
        title="VPN is not connecting",
        description="Employee cannot connect to corporate VPN.",
        created_at=now,
        updated_at=now,
    )

    assert ticket.status == TicketStatus.NEW
    assert ticket.type == TicketType.INCIDENT

def test_ticket_requires_title() -> None:
    now = datetime.now(timezone.utc)

    with pytest.raises(ValidationError):
        Ticket(
            ticket_id="INC-002",
            user_id="USR-001",
            type=TicketType.INCIDENT,
            title="",
            description="VPN is not connecting.",
            created_at=now,
            updated_at=now,
        )