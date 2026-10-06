from datetime import datetime, timezone

import pytest

from app.domain.enums import (
    TicketStatus,
    TicketType,
)
from app.domain.ticket import Ticket
from app.infrastructure.itsm.mock_servicenow_client import (
    MockServiceNowClient,
)


def create_incident() -> Ticket:
    now = datetime.now(timezone.utc)

    return Ticket(
        ticket_id="TKT-001",
        user_id="USR-001",
        type=TicketType.INCIDENT,
        status=TicketStatus.OPEN,
        title="VPN connection failure",
        description=(
            "Employee cannot connect to the corporate VPN."
        ),
        created_at=now,
        updated_at=now,
    )


def create_request() -> Ticket:
    now = datetime.now(timezone.utc)

    return Ticket(
        ticket_id="TKT-002",
        user_id="USR-002",
        type=TicketType.REQUEST,
        status=TicketStatus.OPEN,
        title="Request additional monitor",
        description=(
            "Employee requires an additional monitor."
        ),
        created_at=now,
        updated_at=now,
    )


def test_create_incident() -> None:
    client = MockServiceNowClient()

    ticket = create_incident()

    result = client.create_incident(
        ticket
    )

    assert result.external_system == (
        "mock_servicenow"
    )

    assert result.external_id

    assert result.external_number.startswith(
        "INC"
    )

    assert result.ticket_type == (
        TicketType.INCIDENT
    )

    assert result.status == (
        TicketStatus.OPEN.value
    )


def test_create_service_request() -> None:
    client = MockServiceNowClient()

    ticket = create_request()

    result = client.create_service_request(
        ticket
    )

    assert result.external_system == (
        "mock_servicenow"
    )

    assert result.external_id

    assert result.external_number.startswith(
        "REQ"
    )

    assert result.ticket_type == (
        TicketType.REQUEST
    )


def test_incident_creation_rejects_request_ticket() -> None:
    client = MockServiceNowClient()

    with pytest.raises(
        ValueError,
        match="requires an incident ticket",
    ):
        client.create_incident(
            create_request()
        )


def test_request_creation_rejects_incident_ticket() -> None:
    client = MockServiceNowClient()

    with pytest.raises(
        ValueError,
        match="requires a request ticket",
    ):
        client.create_service_request(
            create_incident()
        )


def test_get_ticket_returns_created_record() -> None:
    client = MockServiceNowClient()

    created = client.create_incident(
        create_incident()
    )

    retrieved = client.get_ticket(
        created.external_id
    )

    assert retrieved is not None

    assert (
        retrieved.external_id
        == created.external_id
    )

    assert (
        retrieved.external_number
        == created.external_number
    )


def test_get_unknown_ticket_returns_none() -> None:
    client = MockServiceNowClient()

    result = client.get_ticket(
        "does-not-exist"
    )

    assert result is None


def test_update_ticket() -> None:
    client = MockServiceNowClient()

    created = client.create_incident(
        create_incident()
    )

    updated = client.update_ticket(
        created.external_id,
        status=TicketStatus.RESOLVED,
    )

    assert updated.external_id == (
        created.external_id
    )

    assert updated.status == (
        TicketStatus.RESOLVED.value
    )

    assert updated.updated_at >= (
        created.updated_at
    )


def test_update_unknown_ticket_is_rejected() -> None:
    client = MockServiceNowClient()

    with pytest.raises(
        KeyError,
        match="External ticket not found",
    ):
        client.update_ticket(
            "does-not-exist",
            status=TicketStatus.RESOLVED,
        )


def test_mock_tracks_multiple_records() -> None:
    client = MockServiceNowClient()

    client.create_incident(
        create_incident()
    )

    client.create_service_request(
        create_request()
    )

    assert client.count() == 2


def test_clear_removes_all_records() -> None:
    client = MockServiceNowClient()

    client.create_incident(
        create_incident()
    )

    assert client.count() == 1

    client.clear()

    assert client.count() == 0