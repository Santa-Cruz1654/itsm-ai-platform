from datetime import datetime, timezone

from app.domain.automation import (
    AutomationAction,
    Consent,
    ExecutionResult,
    PolicyResult,
    ValidationResult,
)
from app.domain.enums import (
    AutomationStatus,
    ConsentSource,
    ExecutionStatus,
    PolicyDecision,
    ValidationStatus,
)


def test_successful_password_reset_does_not_require_ticket() -> None:
    now = datetime.now(timezone.utc)

    action = AutomationAction(
        action_id="AUTO-001",
        user_id="USR-001",
        action="password_reset",
        tool="password_reset",

        status=AutomationStatus.COMPLETED,

        consent=Consent(
            granted=True,
            source=ConsentSource.EXPLICIT_USER_REQUEST,
            action="password_reset",
            timestamp=now,
        ),

        policy=PolicyResult(
            decision=PolicyDecision.ALLOWED,
            policy_id="password-reset-v1",
            evaluated_at=now,
        ),

        execution=ExecutionResult(
            status=ExecutionStatus.COMPLETED,
            started_at=now,
            completed_at=now,
        ),

        validation=ValidationResult(
            status=ValidationStatus.PASSED,
            checks=["password_reset_confirmed"],
            validated_at=now,
        ),

        result="password_reset_successful",

        created_at=now,
        completed_at=now,
    )

    assert action.status == AutomationStatus.COMPLETED
    assert action.ticket_id is None
    assert action.consent.granted is True
    assert action.policy.decision == PolicyDecision.ALLOWED
    assert action.execution.status == ExecutionStatus.COMPLETED
    assert action.validation.status == ValidationStatus.PASSED
def test_password_reset_without_user_consent_is_not_authorized() -> None:
    now = datetime.now(timezone.utc)

    action = AutomationAction(
        action_id="AUTO-002",
        user_id="USR-001",
        action="password_reset",
        tool="password_reset",

        status=AutomationStatus.POLICY_CHECK,

        consent=Consent(
            granted=False,
            source=ConsentSource.NOT_REQUIRED,
            action="password_reset",
            timestamp=now,
        ),

        policy=PolicyResult(
            decision=PolicyDecision.ALLOWED,
            policy_id="password-reset-v1",
            evaluated_at=now,
        ),

        execution=ExecutionResult(
            status=ExecutionStatus.PENDING,
        ),

        validation=ValidationResult(
            status=ValidationStatus.PENDING,
        ),

        created_at=now,
    )

    assert action.consent.granted is False
    assert action.policy.decision == PolicyDecision.ALLOWED
    assert action.execution.status == ExecutionStatus.PENDING

    # Policy authorization alone must not imply execution.
    assert action.status == AutomationStatus.POLICY_CHECK

def test_denied_policy_prevents_execution() -> None:
    now = datetime.now(timezone.utc)

    action = AutomationAction(
        action_id="AUTO-003",
        user_id="USR-001",
        action="password_reset",
        tool="password_reset",

        status=AutomationStatus.DENIED,

        consent=Consent(
            granted=True,
            source=ConsentSource.EXPLICIT_USER_REQUEST,
            action="password_reset",
            timestamp=now,
        ),

        policy=PolicyResult(
            decision=PolicyDecision.DENIED,
            policy_id="password-reset-v1",
            evaluated_at=now,
        ),

        execution=ExecutionResult(
            status=ExecutionStatus.PENDING,
        ),

        validation=ValidationResult(
            status=ValidationStatus.PENDING,
        ),

        created_at=now,
    )

    assert action.consent.granted is True
    assert action.policy.decision == PolicyDecision.DENIED
    assert action.status == AutomationStatus.DENIED
    assert action.execution.status == ExecutionStatus.PENDING
