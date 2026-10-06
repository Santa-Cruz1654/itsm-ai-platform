from datetime import datetime, timezone

from app.domain.audit import AuditEvent


def test_self_service_resolution_can_be_audited_without_incident() -> None:
    now = datetime.now(timezone.utc)

    event = AuditEvent(
        event_id="EVENT-001",
        event_type="self_service_resolved",
        user_id="USR-001",
        conversation_id="CONV-001",
        actor="ai_assistant",
        description="Employee confirmed that the VPN issue was resolved through approved self-service guidance.",
        metadata={
            "resolution_type": "self_service",
            "knowledge_article": "KB-VPN-001",
        },
        created_at=now,
    )

    assert event.event_type == "self_service_resolved"
    assert event.conversation_id == "CONV-001"
    assert event.ticket_id is None
    assert event.action_id is None


def test_automation_completion_can_be_audited_without_incident() -> None:
    now = datetime.now(timezone.utc)

    event = AuditEvent(
        event_id="EVENT-002",
        event_type="automation_completed",
        user_id="USR-001",
        action_id="AUTO-001",
        actor="automation_service",
        description="Password reset completed successfully.",
        metadata={
            "action": "password_reset",
            "execution_status": "completed",
            "validation_status": "passed",
        },
        created_at=now,
    )

    assert event.event_type == "automation_completed"
    assert event.action_id == "AUTO-001"
    assert event.ticket_id is None
    