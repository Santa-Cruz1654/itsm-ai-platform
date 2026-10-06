from __future__ import annotations

from typing import Any

from app.application.intent.intent_router import (
    IntentRouter,
    WorkflowRoute,
)
from app.application.intent.intent_workflow_service import (
    IntentWorkflowService,
)
from app.domain.enums import (
    ConfidenceLevel,
    IntentType,
    TicketType,
)
from app.domain.intent import AIIntentAnalysis


# ----------------------------------------------------------------------
# Test data
# ----------------------------------------------------------------------


def create_analysis(
    *,
    intent: IntentType,
    confidence: ConfidenceLevel,
    automation_candidate: bool = False,
) -> AIIntentAnalysis:
    """
    Create a deterministic AIIntentAnalysis for unit tests.
    """

    return AIIntentAnalysis(
        intent=intent,
        category="network",
        subcategory="vpn",
        priority="P2",
        impact="medium",
        urgency="high",
        assignment_group="network_support",
        summary=(
            "Employee reports that the VPN is unavailable."
        ),
        confidence=confidence,
        automation_candidate=automation_candidate,
        software_name=None,
    )


# ----------------------------------------------------------------------
# Fakes
# ----------------------------------------------------------------------


class FakeIntentAnalyzer:
    """
    Test double for IntentAnalyzer.

    It records the exact request received by the workflow.
    """

    def __init__(
        self,
        analysis: AIIntentAnalysis,
    ) -> None:
        self.analysis = analysis
        self.requests: list[str] = []

    def analyze(
        self,
        employee_request: str,
    ) -> AIIntentAnalysis:
        self.requests.append(employee_request)

        return self.analysis


class FakeKnowledgeRetrievalService:
    """
    Test double for KnowledgeRetrievalService.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def search(
        self,
        query: str,
        *,
        mode: str = "hybrid",
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "query": query,
                "mode": mode,
                "limit": limit,
                "filters": filters,
            }
        )

        return {
            "status": "answered",
            "query": query,
            "mode": mode,
            "results": [],
        }
class FakeTicketService:
    """
    Test double matching the real TicketService.create_ticket()
    and TicketService.escalate_ticket() contracts.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.tickets: dict[str, Any] = {}

    def create_ticket(
        self,
        *,
        ticket_type: TicketType,
        title: str,
        description: str,
        user_id: str,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "ticket_type": ticket_type,
                "title": title,
                "description": description,
                "user_id": user_id,
            }
        )

        ticket = {
            "status": "created",
            "ticket_id": "INC-TEST-001",
            "type": ticket_type,
            "title": title,
            "description": description,
            "user_id": user_id,
        }

        self.tickets["INC-TEST-001"] = ticket

        return ticket

    def escalate_ticket(self, ticket_id: str) -> dict[str, Any]:
        ticket = self.tickets[ticket_id]

        ticket["status"] = "escalated"

        return ticket

# ----------------------------------------------------------------------
# Service construction helper
# ----------------------------------------------------------------------


def build_service(
    *,
    analysis: AIIntentAnalysis,
    knowledge_retrieval_service=None,
    ticket_service=None,
) -> IntentWorkflowService:
    """
    Build an IntentWorkflowService with deterministic test doubles.
    """

    return IntentWorkflowService(
        intent_analyzer=FakeIntentAnalyzer(
            analysis
        ),
        intent_router=IntentRouter(),
        knowledge_retrieval_service=(
            knowledge_retrieval_service
        ),
        ticket_service=ticket_service,
    )


# ----------------------------------------------------------------------
# Knowledge workflow
# ----------------------------------------------------------------------


def test_high_confidence_knowledge_question_reaches_rag():
    knowledge_service = (
        FakeKnowledgeRetrievalService()
    )

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.KNOWLEDGE_QUESTION,
            confidence=ConfidenceLevel.HIGH,
        ),
        knowledge_retrieval_service=knowledge_service,
    )

    result = service.handle(
        "How do I connect to the company VPN?"
    )

    assert result.decision.route == (
        WorkflowRoute.RAG
    )

    assert result.response["status"] == (
        "answered"
    )

    assert len(knowledge_service.calls) == 1

    call = knowledge_service.calls[0]

    assert call["query"] == (
        "How do I connect to the company VPN?"
    )

    assert call["mode"] == "hybrid"

    assert call["limit"] == 5

    assert call["filters"] == {
        "category": "network",
        "subcategory": "vpn",
    }


def test_knowledge_question_without_retrieval_service_stops_safely():
    service = build_service(
        analysis=create_analysis(
            intent=IntentType.KNOWLEDGE_QUESTION,
            confidence=ConfidenceLevel.HIGH,
        ),
    )

    result = service.handle(
        "How do I connect to the company VPN?"
    )

    assert result.decision.route == (
        WorkflowRoute.RAG
    )

    assert result.response["status"] == (
        "knowledge_retrieval_required"
    )


# ----------------------------------------------------------------------
# Incident workflow
# ----------------------------------------------------------------------


def test_high_confidence_incident_reaches_ticket_service():
    ticket_service = FakeTicketService()

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.INCIDENT,
            confidence=ConfidenceLevel.HIGH,
        ),
        ticket_service=ticket_service,
    )

    result = service.handle(
        "My VPN is not working.",
        user_id="USR-001",
    )

    assert result.decision.route == (
        WorkflowRoute.TICKET
    )

    assert result.response["status"] == (
        "created"
    )

    assert len(ticket_service.calls) == 1

    call = ticket_service.calls[0]

    assert call["ticket_type"] == (
        TicketType.INCIDENT
    )

    assert call["title"] == (
        "Employee reports that the VPN is unavailable."
    )

    assert call["description"] == (
        "My VPN is not working."
    )

    assert call["user_id"] == "USR-001"


def test_incident_without_ticket_service_stops_safely():
    service = build_service(
        analysis=create_analysis(
            intent=IntentType.INCIDENT,
            confidence=ConfidenceLevel.HIGH,
        ),
    )

    result = service.handle(
        "My VPN is not working.",
        user_id="USR-001",
    )

    assert result.decision.route == (
        WorkflowRoute.TICKET
    )

    assert result.response["status"] == (
        "ticket_creation_required"
    )


def test_incident_without_user_context_does_not_create_ticket():
    ticket_service = FakeTicketService()

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.INCIDENT,
            confidence=ConfidenceLevel.HIGH,
        ),
        ticket_service=ticket_service,
    )

    result = service.handle(
        "My VPN is not working.",
    )

    assert result.decision.route == (
        WorkflowRoute.TICKET
    )

    assert result.response["status"] == (
        "user_context_required"
    )

    assert ticket_service.calls == []


# ----------------------------------------------------------------------
# Service request workflow
# ----------------------------------------------------------------------


def test_high_confidence_service_request_reaches_ticket_service():
    ticket_service = FakeTicketService()

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.SERVICE_REQUEST,
            confidence=ConfidenceLevel.HIGH,
        ),
        ticket_service=ticket_service,
    )

    result = service.handle(
        "Please install the VPN client.",
        user_id="USR-001",
    )

    assert result.decision.route == (
        WorkflowRoute.SERVICE_REQUEST
    )

    assert result.response["status"] == (
        "created"
    )

    assert len(ticket_service.calls) == 1

    call = ticket_service.calls[0]

    assert call["ticket_type"] == (
        TicketType.REQUEST
    )

    assert call["description"] == (
        "Please install the VPN client."
    )

    assert call["user_id"] == "USR-001"


def test_service_request_without_user_context_does_not_create_ticket():
    ticket_service = FakeTicketService()

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.SERVICE_REQUEST,
            confidence=ConfidenceLevel.HIGH,
        ),
        ticket_service=ticket_service,
    )

    result = service.handle(
        "Please install the VPN client.",
    )

    assert result.decision.route == (
        WorkflowRoute.SERVICE_REQUEST
    )

    assert result.response["status"] == (
        "user_context_required"
    )

    assert ticket_service.calls == []


# ----------------------------------------------------------------------
# Automation boundary
# ----------------------------------------------------------------------


def test_high_confidence_automatable_issue_stops_at_review():
    service = build_service(
        analysis=create_analysis(
            intent=IntentType.AUTOMATABLE_ISSUE,
            confidence=ConfidenceLevel.HIGH,
            automation_candidate=True,
        ),
    )

    result = service.handle(
        "My password has expired.",
        user_id="USR-001",
    )

    assert result.decision.route == (
        WorkflowRoute.AUTOMATION_REVIEW
    )

    assert result.response["status"] == (
        "automation_review_required"
    )

    assert result.response[
        "automation_candidate"
    ] is True


def test_automation_candidate_does_not_execute_any_action():
    """
    The workflow must stop at the automation-review boundary.

    No AutomationService exists in this test intentionally.
    The fact that the workflow succeeds without one proves that
    classification alone cannot trigger execution.
    """

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.AUTOMATABLE_ISSUE,
            confidence=ConfidenceLevel.HIGH,
            automation_candidate=True,
        ),
    )

    result = service.handle(
        "Reset my password.",
        user_id="USR-001",
    )

    assert result.decision.route == (
        WorkflowRoute.AUTOMATION_REVIEW
    )

    assert result.response["status"] == (
        "automation_review_required"
    )


# ----------------------------------------------------------------------
# Confirmation boundary
# ----------------------------------------------------------------------


def test_medium_confidence_stops_for_confirmation():
    ticket_service = FakeTicketService()

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.INCIDENT,
            confidence=ConfidenceLevel.MEDIUM,
        ),
        ticket_service=ticket_service,
    )

    result = service.handle(
        "Something might be wrong with my VPN.",
        user_id="USR-001",
    )

    assert result.decision.route == (
        WorkflowRoute.CONFIRMATION_REQUIRED
    )

    assert result.decision.requires_confirmation is True

    assert result.response["status"] == (
        "confirmation_required"
    )

    assert ticket_service.calls == []


# ----------------------------------------------------------------------
# Escalation boundary
# ----------------------------------------------------------------------


def test_low_confidence_stops_for_escalation():
    ticket_service = FakeTicketService()

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.INCIDENT,
            confidence=ConfidenceLevel.LOW,
        ),
        ticket_service=ticket_service,
    )

    result = service.handle(
        "I don't know, something is wrong.",
        user_id="USR-001",
    )

    assert result.decision.route == (
        WorkflowRoute.ESCALATION
    )

    assert result.decision.requires_human_escalation is True

    assert result.response["status"] == (
        "escalation_required"
    )

    assert ticket_service.calls == []


def test_unknown_does_not_reach_ticket_service():
    ticket_service = FakeTicketService()

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.UNKNOWN,
            confidence=ConfidenceLevel.HIGH,
        ),
        ticket_service=ticket_service,
    )

    result = service.handle(
        "How do I repair my refrigerator?",
        user_id="USR-001",
    )

    assert result.decision.route == (
        WorkflowRoute.ESCALATION
    )

    assert result.response["status"] == (
        "escalation_required"
    )

    assert ticket_service.calls == []


# ----------------------------------------------------------------------
# Analyzer boundary
# ----------------------------------------------------------------------


def test_analyzer_receives_original_employee_request():
    analysis = create_analysis(
        intent=IntentType.INCIDENT,
        confidence=ConfidenceLevel.HIGH,
    )

    analyzer = FakeIntentAnalyzer(
        analysis
    )

    service = IntentWorkflowService(
        intent_analyzer=analyzer,
        intent_router=IntentRouter(),
    )

    result = service.handle(
        "My laptop cannot connect to Wi-Fi."
    )

    assert analyzer.requests == [
        "My laptop cannot connect to Wi-Fi."
    ]

    assert result.analysis == analysis

    assert result.decision.route == (
        WorkflowRoute.TICKET
    )

    assert result.response["status"] == (
        "ticket_creation_required"
    )


# ----------------------------------------------------------------------
# Result contract
# ----------------------------------------------------------------------


def test_workflow_result_contains_analysis_and_decision():
    analysis = create_analysis(
        intent=IntentType.INCIDENT,
        confidence=ConfidenceLevel.HIGH,
    )

    ticket_service = FakeTicketService()

    service = build_service(
        analysis=analysis,
        ticket_service=ticket_service,
    )

    result = service.handle(
        "VPN is broken.",
        user_id="USR-001",
    )

    assert result.analysis == analysis

    assert result.decision.route == (
        WorkflowRoute.TICKET
    )

    assert result.response["status"] == (
        "created"
    )


# ----------------------------------------------------------------------
# Dependency isolation
# ----------------------------------------------------------------------


def test_routing_does_not_call_unrelated_services():
    knowledge_service = (
        FakeKnowledgeRetrievalService()
    )

    ticket_service = FakeTicketService()

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.INCIDENT,
            confidence=ConfidenceLevel.HIGH,
        ),
        knowledge_retrieval_service=knowledge_service,
        ticket_service=ticket_service,
    )

    service.handle(
        "VPN is broken.",
        user_id="USR-001",
    )

    assert len(ticket_service.calls) == 1

    assert knowledge_service.calls == []


def test_knowledge_route_does_not_call_ticket_service():
    knowledge_service = (
        FakeKnowledgeRetrievalService()
    )

    ticket_service = FakeTicketService()

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.KNOWLEDGE_QUESTION,
            confidence=ConfidenceLevel.HIGH,
        ),
        knowledge_retrieval_service=knowledge_service,
        ticket_service=ticket_service,
    )

    service.handle(
        "How do I configure the VPN?",
        user_id="USR-001",
    )

    assert len(knowledge_service.calls) == 1

    assert ticket_service.calls == []


def test_confirmation_does_not_call_downstream_services():
    knowledge_service = (
        FakeKnowledgeRetrievalService()
    )

    ticket_service = FakeTicketService()

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.INCIDENT,
            confidence=ConfidenceLevel.MEDIUM,
        ),
        knowledge_retrieval_service=knowledge_service,
        ticket_service=ticket_service,
    )

    result = service.handle(
        "Maybe my VPN is broken.",
        user_id="USR-001",
    )

    assert result.decision.route == (
        WorkflowRoute.CONFIRMATION_REQUIRED
    )

    assert knowledge_service.calls == []

    assert ticket_service.calls == []


def test_escalation_does_not_call_downstream_services():
    knowledge_service = (
        FakeKnowledgeRetrievalService()
    )

    ticket_service = FakeTicketService()

    service = build_service(
        analysis=create_analysis(
            intent=IntentType.UNKNOWN,
            confidence=ConfidenceLevel.LOW,
        ),
        knowledge_retrieval_service=knowledge_service,
        ticket_service=ticket_service,
    )

    result = service.handle(
        "Something weird happened.",
        user_id="USR-001",
    )

    assert result.decision.route == (
        WorkflowRoute.ESCALATION
    )

    assert knowledge_service.calls == []

    assert ticket_service.calls == []