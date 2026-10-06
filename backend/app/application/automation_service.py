from datetime import datetime, timezone
from uuid import uuid4

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


class AutomationService:
    """
    Application service responsible for the automation lifecycle.

    The service deliberately separates:

    - consent
    - policy authorization
    - execution
    - validation

    Policy authorization does not imply user consent.
    User consent does not bypass policy authorization.
    """

    def create_action(
        self,
        *,
        user_id: str,
        action: str,
        tool: str,
        policy_id: str,
        policy_decision: PolicyDecision,
        consent_granted: bool,
        consent_source: ConsentSource,
        ticket_id: str | None = None,
        conversation_id: str | None = None,
    ) -> AutomationAction:
        if not user_id.strip():
            raise ValueError("User ID cannot be empty.")

        if not action.strip():
            raise ValueError("Automation action cannot be empty.")

        if not tool.strip():
            raise ValueError("Automation tool cannot be empty.")

        if not policy_id.strip():
            raise ValueError("Policy ID cannot be empty.")

        if consent_source == ConsentSource.NOT_REQUIRED and consent_granted:
            raise ValueError(
                "Consent cannot be granted when consent is marked as not required."
            )

        now = datetime.now(timezone.utc)

        return AutomationAction(
            action_id=f"AUTO-{uuid4()}",
            user_id=user_id.strip(),
            ticket_id=ticket_id,
            conversation_id=conversation_id,
            action=action.strip(),
            tool=tool.strip(),
            status=AutomationStatus.POLICY_CHECK,
            consent=Consent(
                granted=consent_granted,
                source=consent_source,
                action=action.strip(),
                timestamp=now,
            ),
            policy=PolicyResult(
                decision=policy_decision,
                policy_id=policy_id.strip(),
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

    def authorize(
        self,
        action: AutomationAction,
    ) -> AutomationAction:
        if action.status != AutomationStatus.POLICY_CHECK:
            raise ValueError(
                "Automation action must be in policy_check status."
            )

        if action.policy.decision == PolicyDecision.DENIED:
            action.status = AutomationStatus.DENIED
            return action

        if not action.consent.granted:
            return action

        action.status = AutomationStatus.AUTHORIZED

        return action

    def execute(
        self,
        action: AutomationAction,
    ) -> AutomationAction:
        if action.status != AutomationStatus.AUTHORIZED:
            raise ValueError(
                "Automation action must be authorized before execution."
            )

        now = datetime.now(timezone.utc)

        action.status = AutomationStatus.EXECUTING
        action.execution.status = ExecutionStatus.RUNNING
        action.execution.started_at = now

        return action

    def complete(
        self,
        action: AutomationAction,
        *,
        result: str,
        validation_checks: list[str],
    ) -> AutomationAction:
        if action.status != AutomationStatus.EXECUTING:
            raise ValueError(
                "Automation action must be executing before completion."
            )

        if not result.strip():
            raise ValueError("Automation result cannot be empty.")

        if not validation_checks:
            raise ValueError(
                "At least one validation check is required."
            )

        now = datetime.now(timezone.utc)

        action.status = AutomationStatus.VALIDATING
        action.execution.status = ExecutionStatus.COMPLETED
        action.execution.completed_at = now

        action.validation.status = ValidationStatus.PASSED
        action.validation.checks = validation_checks
        action.validation.validated_at = now

        action.result = result.strip()
        action.completed_at = now
        action.status = AutomationStatus.COMPLETED

        return action

    def fail(
        self,
        action: AutomationAction,
        *,
        error: str,
    ) -> AutomationAction:
        if not error.strip():
            raise ValueError("Automation error cannot be empty.")

        now = datetime.now(timezone.utc)

        action.execution.status = ExecutionStatus.FAILED
        action.execution.completed_at = now
        action.execution.error = error.strip()

        action.validation.status = ValidationStatus.FAILED
        action.validation.validated_at = now

        action.status = AutomationStatus.FAILED

        return action