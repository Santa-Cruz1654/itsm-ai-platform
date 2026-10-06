from fastapi.testclient import TestClient

from app.main import app


def test_create_incident_ticket() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tickets",
            json={
                "type": "incident",
                "title": "VPN connection failure",
                "description": "Employee cannot connect to the corporate VPN.",
                "user_id": "USR-001",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["ticket_id"].startswith("TKT-")
    assert data["type"] == "incident"
    assert data["status"] == "open"
    assert data["title"] == "VPN connection failure"
    assert data["description"] == (
        "Employee cannot connect to the corporate VPN."
    )
    assert data["user_id"] == "USR-001"

    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_create_request_ticket() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tickets",
            json={
                "type": "request",
                "title": "Request additional monitor",
                "description": "Employee requires an additional monitor.",
                "user_id": "USR-002",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["ticket_id"].startswith("TKT-")
    assert data["type"] == "request"
    assert data["status"] == "open"
    assert data["user_id"] == "USR-002"


def test_create_ticket_rejects_empty_title() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tickets",
            json={
                "type": "incident",
                "title": "",
                "description": "Employee cannot connect to VPN.",
                "user_id": "USR-001",
            },
        )

    assert response.status_code == 422


def test_create_ticket_rejects_empty_description() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tickets",
            json={
                "type": "incident",
                "title": "VPN connection failure",
                "description": "",
                "user_id": "USR-001",
            },
        )

    assert response.status_code == 422


def test_create_ticket_rejects_empty_user_id() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tickets",
            json={
                "type": "incident",
                "title": "VPN connection failure",
                "description": "Employee cannot connect to VPN.",
                "user_id": "",
            },
        )

    assert response.status_code == 422


def test_create_ticket_rejects_invalid_ticket_type() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tickets",
            json={
                "type": "invalid_type",
                "title": "VPN connection failure",
                "description": "Employee cannot connect to VPN.",
                "user_id": "USR-001",
            },
        )

    assert response.status_code == 422


def test_create_ticket_rejects_unknown_fields() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tickets",
            json={
                "type": "incident",
                "title": "VPN connection failure",
                "description": "Employee cannot connect to VPN.",
                "user_id": "USR-001",
                "unknown_field": "should be rejected",
            },
        )

    assert response.status_code == 422