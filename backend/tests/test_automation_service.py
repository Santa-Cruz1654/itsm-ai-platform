from app.application.automation_service import AutomationService
from app.domain.enums import (
    AutomationStatus,
    ConsentSource,
    ExecutionStatus,
    PolicyDecision,
    ValidationStatus,
)


def create_service() -> AutomationService:
    return AutomationService()


def test_create_automation_action() -> None:
    service = create_service()

    action = service.create_action(
        user_id="USR-001",
        action="password_reset",
        tool="password_reset",
        policy_id="password-reset-v1",
        policy_decision=PolicyDecision.ALLOWED,
        consent_granted=True,
        consent_source=ConsentSource.EXPLICIT_USER_REQUEST,
    )

    assert action.action.startswith("password_reset")
    assert action.user_id == "USR-001"
    assert action.status == AutomationStatus.POLICY_CHECK
    assert action.consent.granted is True
    assert (
        action.consent.source
        == ConsentSource.EXPLICIT_USER_REQUEST
    )
    assert action.policy.decision == PolicyDecision.ALLOWED
    assert action.execution.status == ExecutionStatus.PENDING
    assert action.validation.status == ValidationStatus.PENDING


def test_policy_authorization_requires_consent() -> None:
    service = create_service()

    action = service.create_action(
        user_id="USR-001",
        action="password_reset",
        tool="password_reset",
        policy_id="password-reset-v1",
        policy_decision=PolicyDecision.ALLOWED,
        consent_granted=False,
        consent_source=ConsentSource.NOT_REQUIRED,
    )

    result = service.authorize(action)

    assert result.status == AutomationStatus.POLICY_CHECK
    assert result.policy.decision == PolicyDecision.ALLOWED
    assert result.consent.granted is False
    assert result.execution.status == ExecutionStatus.PENDING


def test_allowed_policy_and_consent_authorize_action() -> None:
    service = create_service()

    action = service.create_action(
        user_id="USR-001",
        action="password_reset",
        tool="password_reset",
        policy_id="password-reset-v1",
        policy_decision=PolicyDecision.ALLOWED,
        consent_granted=True,
        consent_source=ConsentSource.EXPLICIT_USER_REQUEST,
    )

    result = service.authorize(action)

    assert result.status == AutomationStatus.AUTHORIZED


def test_denied_policy_prevents_execution() -> None:
    service = create_service()

    action = service.create_action(
        user_id="USR-001",
        action="password_reset",
        tool="password_reset",
        policy_id="password-reset-v1",
        policy_decision=PolicyDecision.DENIED,
        consent_granted=True,
        consent_source=ConsentSource.EXPLICIT_USER_REQUEST,
    )

    result = service.authorize(action)

    assert result.status == AutomationStatus.DENIED
    assert result.execution.status == ExecutionStatus.PENDING


def test_cannot_execute_unauthorized_action() -> None:
    service = create_service()

    action = service.create_action(
        user_id="USR-001",
        action="password_reset",
        tool="password_reset",
        policy_id="password-reset-v1",
        policy_decision=PolicyDecision.ALLOWED,
        consent_granted=False,
        consent_source=ConsentSource.NOT_REQUIRED,
    )

    try:
        service.execute(action)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "authorized before execution" in str(exc)


def test_execute_authorized_action() -> None:
    service = create_service()

    action = service.create_action(
        user_id="USR-001",
        action="password_reset",
        tool="password_reset",
        policy_id="password-reset-v1",
        policy_decision=PolicyDecision.ALLOWED,
        consent_granted=True,
        consent_source=ConsentSource.EXPLICIT_USER_REQUEST,
    )

    service.authorize(action)
    result = service.execute(action)

    assert result.status == AutomationStatus.EXECUTING
    assert result.execution.status == ExecutionStatus.RUNNING
    assert result.execution.started_at is not None


def test_complete_successful_automation() -> None:
    service = create_service()

    action = service.create_action(
        user_id="USR-001",
        action="password_reset",
        tool="password_reset",
        policy_id="password-reset-v1",
        policy_decision=PolicyDecision.ALLOWED,
        consent_granted=True,
        consent_source=ConsentSource.EXPLICIT_USER_REQUEST,
    )

    service.authorize(action)
    service.execute(action)

    result = service.complete(
        action,
        result="password_reset_successful",
        validation_checks=["password_reset_confirmed"],
    )

    assert result.status == AutomationStatus.COMPLETED
    assert result.execution.status == ExecutionStatus.COMPLETED
    assert result.validation.status == ValidationStatus.PASSED
    assert result.result == "password_reset_successful"
    assert result.completed_at is not None
    assert result.ticket_id is None


def test_failed_automation() -> None:
    service = create_service()

    action = service.create_action(
        user_id="USR-001",
        action="password_reset",
        tool="password_reset",
        policy_id="password-reset-v1",
        policy_decision=PolicyDecision.ALLOWED,
        consent_granted=True,
        consent_source=ConsentSource.EXPLICIT_USER_REQUEST,
    )

    service.authorize(action)
    service.execute(action)

    result = service.fail(
        action,
        error="Password reset provider unavailable.",
    )

    assert result.status == AutomationStatus.FAILED
    assert result.execution.status == ExecutionStatus.FAILED
    assert result.execution.error == (
        "Password reset provider unavailable."
    )
    assert result.validation.status == ValidationStatus.FAILED