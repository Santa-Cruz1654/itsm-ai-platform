from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.application.automation_service import (
    AutomationService,
)
from app.application.self_healing_service import (
    SelfHealingWorkflowService,
)
from app.application.ticket_service import (
    TicketService,
)

from app.domain.enums import (
    AutomationStatus,
    ConfidenceLevel,
    ConsentSource,
    IntentType,
    PolicyDecision,
    TicketStatus,
    TicketType,
)
from app.domain.intent import AIIntentAnalysis
from app.infrastructure.automation.mock_password_reset import (
    MockPasswordResetTool,
)
from app.infrastructure.repositories.memory_audit_repository import (
    InMemoryAuditRepository,
)


class FakeKnowledgeRetrievalService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def hybrid_search(
        self,
        query: str,
        *,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
        candidate_limit: int = 20,
    ):
        self.calls.append(query)

        class Metadata:
            title = "Password Reset"
            category = "identity"
            subcategory = "password"

        class Chunk:
            document_id = "DOC-PASSWORD"
            id = "CHUNK-PASSWORD"
            metadata = Metadata()

        class Result:
            chunk = Chunk()
            hybrid_score = 0.91

        return [Result()]


class FakeITSMClient:
    def __init__(self) -> None:
        self.updates: list[dict[str, Any]] = []

    def update_ticket(
        self,
        external_id: str,
        *,
        status=None,
        description=None,
    ):
        self.updates.append(
            {
                "external_id": external_id,
                "status": status,
                "description": description,
            }
        )

        return None


def create_analysis() -> AIIntentAnalysis:
    return AIIntentAnalysis(
        intent=IntentType.AUTOMATABLE_ISSUE,
        category="identity",
        subcategory="password",
        priority="P2",
        impact="individual",
        urgency="high",
        assignment_group="identity_support",
        summary="Password has expired.",
        confidence=ConfidenceLevel.HIGH,
        automation_candidate=True,
        software_name=None,
    )


def create_service(
    *,
    tool: MockPasswordResetTool | None = None,
):
    knowledge = (
        FakeKnowledgeRetrievalService()
    )

    audit = (
        InMemoryAuditRepository()
    )

    itsm = FakeITSMClient()

    password_tool = (
        tool
        if tool is not None
        else MockPasswordResetTool()
    )

    ticket_service = TicketService()

    service = SelfHealingWorkflowService(
        automation_service=(
            AutomationService()
        ),
        knowledge_retrieval_service=knowledge,
        audit_repository=audit,
        ticket_service=ticket_service,
        itsm_client=itsm,
        password_reset_tool=password_tool,
    )

    return (
        service,
        knowledge,
        audit,
        itsm,
        password_tool,
    )

def test_password_reset_self_healing_succeeds() -> None:
    (
        service,
        knowledge,
        audit,
        itsm,
        tool,
    ) = create_service()

    result = service.handle(
        employee_request=(
            "My password has expired."
        ),
        user_id="USR-001",
        analysis=create_analysis(),
        consent_granted=True,
        consent_source=(
            ConsentSource.EXPLICIT_USER_REQUEST
        ),
    )

    assert result.status == "resolved"

    assert result.action == "password_reset"

    assert result.tool == "password_reset"

    assert result.automation_status == (
        AutomationStatus.COMPLETED
    )

    assert result.validation_checks

    assert result.knowledge_sources

    assert len(knowledge.calls) == 1

    assert tool.was_executed_for(
        "USR-001"
    )

    events = audit.get_all()

    event_types = [
        event.event_type
        for event in events
    ]

    assert (
        "self_healing_started"
        in event_types
    )

    assert (
        "self_healing_diagnosed"
        in event_types
    )

    assert (
        "self_healing_knowledge_retrieved"
        in event_types
    )

    assert (
        "automation_execution_started"
        in event_types
    )

    assert (
        "automation_validated"
        in event_types
    )

    assert (
        "self_healing_completed"
        in event_types
    )


def test_password_reset_without_consent_does_not_execute() -> None:
    (
        service,
        _knowledge,
        audit,
        _itsm,
        tool,
    ) = create_service()

    result = service.handle(
        employee_request=(
            "My password has expired."
        ),
        user_id="USR-002",
        analysis=create_analysis(),
        consent_granted=False,
        consent_source=(
            ConsentSource.NOT_REQUIRED
        ),
    )

    assert result.status == (
        "confirmation_required"
    )

    assert tool.was_executed_for(
        "USR-002"
    ) is False

    events = audit.get_all()

    assert any(
        event.event_type
        == "automation_not_authorized"
        for event in events
    )


def test_denied_candidate_is_never_executed() -> None:
    (
        service,
        _knowledge,
        _audit,
        _itsm,
        tool,
    ) = create_service()

    analysis = create_analysis()

    analysis = analysis.model_copy(
        update={
            "automation_candidate": False
        }
    )

    result = service.handle(
        employee_request=(
            "My password has expired."
        ),
        user_id="USR-003",
        analysis=analysis,
        consent_granted=True,
        consent_source=(
            ConsentSource.EXPLICIT_USER_REQUEST
        ),
    )

    assert result.status == (
        "not_automatable"
    )

    assert tool.was_executed_for(
        "USR-003"
    ) is False


def test_missing_knowledge_escalates() -> None:
    class EmptyKnowledge:
        def hybrid_search(
            self,
            query: str,
            *,
            limit: int = 5,
            filters=None,
            candidate_limit: int = 20,
        ):
            return []

    audit = (
        InMemoryAuditRepository()
    )

    tool = MockPasswordResetTool()

    service = SelfHealingWorkflowService(
        automation_service=(
            AutomationService()
        ),
        knowledge_retrieval_service=(
            EmptyKnowledge()
        ),
        audit_repository=audit,
        ticket_service=TicketService(),
        itsm_client=FakeITSMClient(),
        password_reset_tool=tool,
    )

    result = service.handle(
        employee_request=(
            "My password has expired."
        ),
        user_id="USR-004",
        analysis=create_analysis(),
        consent_granted=True,
        consent_source=(
            ConsentSource.EXPLICIT_USER_REQUEST
        ),
    )

    assert result.status == (
        "escalation_required"
    )

    assert tool.was_executed_for(
        "USR-004"
    ) is False


def test_failed_password_reset_does_not_report_success() -> None:
    tool = MockPasswordResetTool(
        should_succeed=False
    )

    (
        service,
        _knowledge,
        audit,
        _itsm,
        _tool,
    ) = create_service(
        tool=tool
    )

    result = service.handle(
        employee_request=(
            "My password has expired."
        ),
        user_id="USR-005",
        analysis=create_analysis(),
        consent_granted=True,
        consent_source=(
            ConsentSource.EXPLICIT_USER_REQUEST
        ),
    )

    assert result.status == (
        "automation_failed"
    )

    assert result.automation_status == (
        AutomationStatus.FAILED
    )

    events = audit.get_all()

    assert any(
        event.event_type
        == "automation_failed"
        for event in events
    )