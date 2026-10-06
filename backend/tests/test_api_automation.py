from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_automation() -> None:
    response = client.post(
        "/api/v1/automations",
        json={
            "user_id": "USR-001",
            "action": "password_reset",
            "tool": "password_reset",
            "policy_id": "password-reset-v1",
            "policy_decision": "allowed",
            "consent_granted": True,
            "consent_source": "explicit_user_request",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == "USR-001"
    assert data["action"] == "password_reset"
    assert data["tool"] == "password_reset"
    assert data["status"] == "policy_check"

    assert data["consent"]["granted"] is True
    assert data["consent"]["source"] == "explicit_user_request"

    assert data["policy"]["decision"] == "allowed"

    assert data["execution"]["status"] == "pending"
    assert data["validation"]["status"] == "pending"


def test_create_automation_rejects_empty_user_id() -> None:
    response = client.post(
        "/api/v1/automations",
        json={
            "user_id": "",
            "action": "password_reset",
            "tool": "password_reset",
            "policy_id": "password-reset-v1",
            "policy_decision": "allowed",
            "consent_granted": True,
            "consent_source": "explicit_user_request",
        },
    )

    assert response.status_code == 422


def test_create_automation_rejects_unknown_fields() -> None:
    response = client.post(
        "/api/v1/automations",
        json={
            "user_id": "USR-001",
            "action": "password_reset",
            "tool": "password_reset",
            "policy_id": "password-reset-v1",
            "policy_decision": "allowed",
            "consent_granted": True,
            "consent_source": "explicit_user_request",
            "unexpected_field": "not_allowed",
        },
    )

    assert response.status_code == 422


def test_create_automation_preserves_policy_and_consent_boundary() -> None:
    response = client.post(
        "/api/v1/automations",
        json={
            "user_id": "USR-001",
            "action": "password_reset",
            "tool": "password_reset",
            "policy_id": "password-reset-v1",
            "policy_decision": "allowed",
            "consent_granted": False,
            "consent_source": "not_required",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["policy"]["decision"] == "allowed"
    assert data["consent"]["granted"] is False
    assert data["status"] == "policy_check"
    assert data["execution"]["status"] == "pending"