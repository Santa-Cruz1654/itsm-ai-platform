from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_intent_workflow_service,
)
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
from app.domain.intent import (
    AIIntentAnalysis,
)
from app.main import app


# ----------------------------------------------------------------------
# Test constants
# ----------------------------------------------------------------------

SAP_REQUEST = (
    "How do I configure the company's "
    "SAP production database replication?"
)

QUANTUM_REQUEST = (
    "Explain quantum gravity and provide "
    "the mathematical derivation."
)


# ----------------------------------------------------------------------
# Test doubles
# ----------------------------------------------------------------------


class FakeIntentAnalyzer:
    """
    Deterministic IntentAnalyzer replacement.

    This avoids invoking the real LLM during unit tests.
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
        self.requests.append(
            employee_request
        )

        return self.analysis


class FakeKnowledgeRetrievalService:
    """
    Retrieval double used to prove that UNKNOWN requests
    never enter the RAG path.
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

        raise AssertionError(
            "UNKNOWN requests must never reach "
            "knowledge retrieval."
        )

class FakeTicketService:
    """
    Deterministic TicketService replacement.

    Matches the actual TicketService.create_ticket()
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
    ) -> Any:
        self.calls.append(
            {
                "ticket_type": ticket_type,
                "title": title,
                "description": description,
                "user_id": user_id,
            }
        )

        class FakeTicket:
            ticket_id = "TKT-PHASE10-001"
            external_ticket_id = (
                "SYSID-PHASE10-001"
            )
            external_ticket_number = (
                "INC0010001"
            )

        ticket = FakeTicket()

        self.tickets[ticket.ticket_id] = ticket

        return ticket

    def escalate_ticket(
        self,
        ticket_id: str,
    ) -> Any:
        ticket = self.tickets[ticket_id]

        # Match the production escalation state.
        ticket.status = "ESCALATED"

        return ticket

# ----------------------------------------------------------------------
# Test analysis factories
# ----------------------------------------------------------------------


def create_unknown_analysis() -> AIIntentAnalysis:
    return AIIntentAnalysis(
        intent=IntentType.UNKNOWN,
        category=None,
        subcategory=None,
        priority=None,
        impact=None,
        urgency=None,
        assignment_group=None,
        summary=(
            "Unsupported enterprise ITSM request."
        ),
        confidence=ConfidenceLevel.HIGH,
        automation_candidate=False,
        software_name=None,
    )


def create_low_confidence_analysis() -> AIIntentAnalysis:
    return AIIntentAnalysis(
        intent=IntentType.INCIDENT,
        category="unknown",
        subcategory="unknown",
        priority=None,
        impact=None,
        urgency=None,
        assignment_group=None,
        summary=(
            "Employee reports an unclear "
            "system problem."
        ),
        confidence=ConfidenceLevel.LOW,
        automation_candidate=False,
        software_name=None,
    )


# ----------------------------------------------------------------------
# Workflow factory
# ----------------------------------------------------------------------


def build_service(
    *,
    analysis: AIIntentAnalysis,
    ticket_service: FakeTicketService | None = None,
):
    analyzer = FakeIntentAnalyzer(
        analysis
    )

    router = IntentRouter()

    knowledge_service = (
        FakeKnowledgeRetrievalService()
    )

    service = IntentWorkflowService(
        intent_analyzer=analyzer,
        intent_router=router,
        knowledge_retrieval_service=(
            knowledge_service
        ),
        ticket_service=ticket_service,
    )

    return (
        service,
        analyzer,
        knowledge_service,
    )


# ----------------------------------------------------------------------
# UNKNOWN routing
# ----------------------------------------------------------------------


def test_unknown_intent_routes_to_escalation():
    service, _, _ = build_service(
        analysis=create_unknown_analysis()
    )

    result = service.handle(
        SAP_REQUEST,
        user_id="USR-PHASE10-001",
    )

    assert (
        result.analysis.intent
        == IntentType.UNKNOWN
    )

    assert (
        result.decision.route
        == WorkflowRoute.ESCALATION
    )

    assert (
        result.decision.requires_human_escalation
        is True
    )


def test_unknown_question_does_not_hallucinate():
    service, _, _ = build_service(
        analysis=create_unknown_analysis()
    )

    result = service.handle(
        SAP_REQUEST,
        user_id="USR-PHASE10-001",
    )

    assert (
        result.decision.route
        == WorkflowRoute.ESCALATION
    )

    assert isinstance(
        result.response,
        dict,
    )

    assert (
        result.response["status"]
        == "escalation_required"
    )

    assert (
        result.response["ticket_created"]
        is False
    )

    assert (
        "couldn't find sufficient approved"
        in result.response["message"].lower()
    )

    assert (
        "knowledge-base"
        in result.response["message"].lower()
    )


def test_sap_production_database_request_is_escalated():
    service, _, _ = build_service(
        analysis=create_unknown_analysis()
    )

    result = service.handle(
        SAP_REQUEST,
        user_id="USR-PHASE10-002",
    )

    assert (
        result.decision.route
        == WorkflowRoute.ESCALATION
    )

    assert (
        result.decision.requires_human_escalation
        is True
    )

    assert (
        result.response["status"]
        == "escalation_required"
    )


def test_quantum_gravity_request_is_not_answered():
    service, _, _ = build_service(
        analysis=create_unknown_analysis()
    )

    result = service.handle(
        QUANTUM_REQUEST,
        user_id="USR-PHASE10-003",
    )

    assert (
        result.decision.route
        == WorkflowRoute.ESCALATION
    )

    assert (
        result.response["status"]
        == "escalation_required"
    )

    assert (
        result.response["ticket_created"]
        is False
    )


# ----------------------------------------------------------------------
# RAG boundary
# ----------------------------------------------------------------------


def test_unknown_request_never_reaches_rag():
    service, _, knowledge_service = (
        build_service(
            analysis=create_unknown_analysis()
        )
    )

    result = service.handle(
        SAP_REQUEST,
        user_id="USR-PHASE10-004",
    )

    assert (
        result.decision.route
        == WorkflowRoute.ESCALATION
    )

    assert (
        knowledge_service.calls == []
    )


# ----------------------------------------------------------------------
# Ticket creation boundary
# ----------------------------------------------------------------------


def test_unknown_request_does_not_create_ticket_implicitly():
    ticket_service = FakeTicketService()

    service, _, _ = build_service(
        analysis=create_unknown_analysis(),
        ticket_service=ticket_service,
    )

    result = service.handle(
        SAP_REQUEST,
        user_id="USR-PHASE10-005",
        create_escalation_ticket=False,
    )

    assert (
        result.decision.route
        == WorkflowRoute.ESCALATION
    )

    assert (
        result.response["ticket_created"]
        is False
    )

    assert (
        ticket_service.calls == []
    )


def test_unknown_request_creates_ticket_when_explicitly_requested():
    ticket_service = FakeTicketService()

    service, _, _ = build_service(
        analysis=create_unknown_analysis(),
        ticket_service=ticket_service,
    )

    result = service.handle(
        SAP_REQUEST,
        user_id="USR-PHASE10-006",
        create_escalation_ticket=True,
    )

    assert (
        result.decision.route
        == WorkflowRoute.ESCALATION
    )

    assert (
        result.response["status"]
        == "escalated"
    )

    assert (
        result.response["ticket_created"]
        is True
    )

    assert (
        result.response["ticket_id"]
        == "TKT-PHASE10-001"
    )

    assert len(
        ticket_service.calls
    ) == 1


def test_escalation_ticket_is_incident():
    ticket_service = FakeTicketService()

    service, _, _ = build_service(
        analysis=create_unknown_analysis(),
        ticket_service=ticket_service,
    )

    service.handle(
        SAP_REQUEST,
        user_id="USR-PHASE10-007",
        create_escalation_ticket=True,
    )

    call = ticket_service.calls[0]

    assert (
        call["ticket_type"]
        == TicketType.INCIDENT
    )


def test_escalation_ticket_preserves_original_request():
    ticket_service = FakeTicketService()

    service, _, _ = build_service(
        analysis=create_unknown_analysis(),
        ticket_service=ticket_service,
    )

    service.handle(
        SAP_REQUEST,
        user_id="USR-PHASE10-008",
        create_escalation_ticket=True,
    )

    call = ticket_service.calls[0]

    assert (
        SAP_REQUEST
        in call["description"]
    )


def test_escalation_ticket_contains_reason():
    ticket_service = FakeTicketService()

    service, _, _ = build_service(
        analysis=create_unknown_analysis(),
        ticket_service=ticket_service,
    )

    service.handle(
        SAP_REQUEST,
        user_id="USR-PHASE10-009",
        create_escalation_ticket=True,
    )

    call = ticket_service.calls[0]

    assert (
        "unknown_intent"
        in call["description"]
    )


# ----------------------------------------------------------------------
# Identity safety
# ----------------------------------------------------------------------


def test_explicit_escalation_without_user_id_does_not_create_ticket():
    ticket_service = FakeTicketService()

    service, _, _ = build_service(
        analysis=create_unknown_analysis(),
        ticket_service=ticket_service,
    )

    result = service.handle(
        SAP_REQUEST,
        user_id=None,
        create_escalation_ticket=True,
    )

    assert (
        result.decision.route
        == WorkflowRoute.ESCALATION
    )

    assert (
        result.response["status"]
        == "user_context_required"
    )

    assert (
        result.response["ticket_created"]
        is False
    )

    assert (
        ticket_service.calls == []
    )


def test_explicit_escalation_with_empty_user_id_does_not_create_ticket():
    ticket_service = FakeTicketService()

    service, _, _ = build_service(
        analysis=create_unknown_analysis(),
        ticket_service=ticket_service,
    )

    result = service.handle(
        SAP_REQUEST,
        user_id="",
        create_escalation_ticket=True,
    )

    assert (
        result.response["status"]
        == "user_context_required"
    )

    assert (
        ticket_service.calls == []
    )


# ----------------------------------------------------------------------
# Missing ticket service
# ----------------------------------------------------------------------


def test_explicit_escalation_without_ticket_service_is_safe():
    service, _, _ = build_service(
        analysis=create_unknown_analysis(),
        ticket_service=None,
    )

    result = service.handle(
        SAP_REQUEST,
        user_id="USR-PHASE10-010",
        create_escalation_ticket=True,
    )

    assert (
        result.decision.route
        == WorkflowRoute.ESCALATION
    )

    assert (
        result.response["status"]
        == "escalation_ticket_unavailable"
    )

    assert (
        result.response["ticket_created"]
        is False
    )


# ----------------------------------------------------------------------
# LOW confidence
# ----------------------------------------------------------------------


def test_low_confidence_routes_to_escalation():
    service, _, _ = build_service(
        analysis=(
            create_low_confidence_analysis()
        )
    )

    result = service.handle(
        "Something strange is happening "
        "with my computer.",
        user_id="USR-PHASE10-011",
    )

    assert (
        result.decision.route
        == WorkflowRoute.ESCALATION
    )

    assert (
        result.decision.requires_human_escalation
        is True
    )


def test_low_confidence_does_not_create_ticket_implicitly():
    ticket_service = FakeTicketService()

    service, _, _ = build_service(
        analysis=(
            create_low_confidence_analysis()
        ),
        ticket_service=ticket_service,
    )

    result = service.handle(
        "Something strange is happening "
        "with my computer.",
        user_id="USR-PHASE10-012",
        create_escalation_ticket=False,
    )

    assert (
        result.decision.route
        == WorkflowRoute.ESCALATION
    )

    assert (
        ticket_service.calls == []
    )


def test_low_confidence_can_create_ticket_explicitly():
    ticket_service = FakeTicketService()

    service, _, _ = build_service(
        analysis=(
            create_low_confidence_analysis()
        ),
        ticket_service=ticket_service,
    )

    result = service.handle(
        "Something strange is happening "
        "with my computer.",
        user_id="USR-PHASE10-013",
        create_escalation_ticket=True,
    )

    assert (
        result.decision.route
        == WorkflowRoute.ESCALATION
    )

    assert (
        result.response["status"]
        == "escalated"
    )

    assert (
        result.response["ticket_created"]
        is True
    )

    assert len(
        ticket_service.calls
    ) == 1


# ----------------------------------------------------------------------
# API tests
# ----------------------------------------------------------------------


@pytest.fixture
def clear_dependency_overrides():
    app.dependency_overrides.clear()

    yield

    app.dependency_overrides.clear()


def test_intent_api_unknown_request_without_ticket(
    clear_dependency_overrides,
):
    workflow, _, _ = build_service(
        analysis=create_unknown_analysis()
    )

    app.dependency_overrides[
        get_intent_workflow_service
    ] = lambda: workflow

    client = TestClient(app)

    response = client.post(
        "/api/v1/intent",
        json={
            "user_id": "USR-PHASE10-API-001",
            "employee_request": SAP_REQUEST,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["analysis"]["intent"]
        == "unknown"
    )

    assert (
        data["decision"]["route"]
        == "escalation"
    )

    assert (
        data["decision"]
        ["requires_human_escalation"]
        is True
    )

    assert (
        data["response"]["status"]
        == "escalation_required"
    )

    assert (
        data["response"]["ticket_created"]
        is False
    )


def test_intent_api_unknown_request_with_ticket(
    clear_dependency_overrides,
):
    ticket_service = FakeTicketService()

    workflow, _, _ = build_service(
        analysis=create_unknown_analysis(),
        ticket_service=ticket_service,
    )

    app.dependency_overrides[
        get_intent_workflow_service
    ] = lambda: workflow

    client = TestClient(app)

    response = client.post(
        "/api/v1/intent",
        json={
            "user_id": "USR-PHASE10-API-002",
            "employee_request": SAP_REQUEST,
            "create_escalation_ticket": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["analysis"]["intent"]
        == "unknown"
    )

    assert (
        data["decision"]["route"]
        == "escalation"
    )

    assert (
        data["response"]["status"]
        == "escalated"
    )

    assert (
        data["response"]["ticket_created"]
        is True
    )

    assert (
        data["response"]["ticket_id"]
        == "TKT-PHASE10-001"
    )

    assert len(
        ticket_service.calls
    ) == 1


def test_intent_api_rejects_unknown_fields(
    clear_dependency_overrides,
):
    workflow, _, _ = build_service(
        analysis=create_unknown_analysis()
    )

    app.dependency_overrides[
        get_intent_workflow_service
    ] = lambda: workflow

    client = TestClient(app)

    response = client.post(
        "/api/v1/intent",
        json={
            "user_id": "USR-PHASE10-API-003",
            "employee_request": SAP_REQUEST,
            "unexpected_field": (
                "must-be-rejected"
            ),
        },
    )

    assert response.status_code == 422