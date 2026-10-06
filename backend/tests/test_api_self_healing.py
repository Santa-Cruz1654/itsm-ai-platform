from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_intent_analyzer,
    get_intent_workflow_service,
    get_self_healing_service,
)
from app.application.automation_service import (
    AutomationService,
)

from app.application.intent.intent_router import (
    IntentRouter,
)
from app.application.intent.intent_workflow_service import (
    IntentWorkflowService,
)
from app.application.self_healing_service import (
    SelfHealingWorkflowService,
)
from app.application.ticket_service import (
    TicketService,
)
from app.domain.enums import (
    ConsentSource,
    ConfidenceLevel,
    IntentType,
)
from app.domain.intent import (
    AIIntentAnalysis,
)
from app.infrastructure.automation.mock_password_reset import (
    MockPasswordResetTool,
)
from app.infrastructure.repositories.memory_audit_repository import (
    InMemoryAuditRepository,
)
from app.main import app


# ----------------------------------------------------------------------
# Test doubles
# ----------------------------------------------------------------------


class FakeIntentAnalyzer:
    """
    Deterministic analyzer for API integration tests.

    This intentionally avoids invoking the real LLM.
    """

    def __init__(
        self,
        analysis: AIIntentAnalysis,
    ) -> None:
        self._analysis = analysis
        self.requests: list[str] = []

    def analyze(
        self,
        employee_request: str,
    ) -> AIIntentAnalysis:
        self.requests.append(
            employee_request,
        )

        return self._analysis


class FakeKnowledgeRetrievalService:
    """
    Deterministic knowledge source for self-healing tests.
    """

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
    """
    Deterministic external ITSM double.
    """

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


# ----------------------------------------------------------------------
# Test data
# ----------------------------------------------------------------------


def create_password_analysis() -> AIIntentAnalysis:
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


# ----------------------------------------------------------------------
# Workflow construction
# ----------------------------------------------------------------------


def create_self_healing_stack():
    knowledge = (
        FakeKnowledgeRetrievalService()
    )

    audit = (
        InMemoryAuditRepository()
    )

    itsm = FakeITSMClient()

    password_tool = (
        MockPasswordResetTool()
    )

    service = SelfHealingWorkflowService(
        automation_service=(
            AutomationService()
        ),
        knowledge_retrieval_service=knowledge,
        audit_repository=audit,
        ticket_service=TicketService(),
        itsm_client=itsm,
        password_reset_tool=password_tool,
    )

    analyzer = FakeIntentAnalyzer(
        create_password_analysis(),
    )

    intent_workflow = IntentWorkflowService(
        intent_analyzer=analyzer,
        intent_router=IntentRouter(),
        knowledge_retrieval_service=knowledge,
        ticket_service=TicketService(),
        self_healing_service=service,
    )

    return (
        service,
        analyzer,
        intent_workflow,
        knowledge,
        audit,
        itsm,
        password_tool,
    )


# ----------------------------------------------------------------------
# Dependency cleanup
# ----------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()

    yield

    app.dependency_overrides.clear()


# ----------------------------------------------------------------------
# Router registration
# ----------------------------------------------------------------------


def test_self_healing_router_is_registered() -> None:
    paths = app.openapi()["paths"]

    assert "/api/v1/self-healing" in paths

    assert (
        "post"
        in paths["/api/v1/self-healing"]
    )


# ----------------------------------------------------------------------
# Direct self-healing API
# ----------------------------------------------------------------------


def test_self_healing_api_executes_password_reset() -> None:
    (
        service,
        analyzer,
        _intent_workflow,
        knowledge,
        audit,
        _itsm,
        password_tool,
    ) = create_self_healing_stack()

    app.dependency_overrides[
        get_intent_analyzer
    ] = lambda: analyzer

    app.dependency_overrides[
        get_self_healing_service
    ] = lambda: service

    client = TestClient(app)

    response = client.post(
        "/api/v1/self-healing",
        json={
            "user_id": "USR-API-001",
            "employee_request": (
                "My password has expired."
            ),
            "consent_granted": True,
            "consent_source": (
                "explicit_user_request"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "resolved"

    assert (
        data["action"]
        == "password_reset"
    )

    assert (
        data["tool"]
        == "password_reset"
    )

    assert data["diagnosis"] == (
        "Password expiry / password reset scenario."
    )

    assert data["validation_checks"]

    assert data["knowledge_sources"]

    assert password_tool.was_executed_for(
        "USR-API-001"
    )

    assert len(
        knowledge.calls
    ) == 1

    assert len(
        audit.get_all()
    ) > 0


# ----------------------------------------------------------------------
# Complete /intent → self-healing path
# ----------------------------------------------------------------------


def test_intent_api_routes_password_expiry_into_self_healing() -> None:
    (
        _service,
        analyzer,
        intent_workflow,
        knowledge,
        audit,
        _itsm,
        password_tool,
    ) = create_self_healing_stack()

    app.dependency_overrides[
        get_intent_workflow_service
    ] = lambda: intent_workflow

    client = TestClient(app)

    response = client.post(
        "/api/v1/intent",
        json={
            "user_id": "USR-API-002",
            "employee_request": (
                "My password has expired."
            ),
            "consent_granted": True,
            "consent_source": (
                "explicit_user_request"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["analysis"]["intent"] == (
        "automatable_issue"
    )

    assert data["analysis"][
        "automation_candidate"
    ] is True

    assert data["decision"]["route"] == (
        "automation_review"
    )

    assert data["response"]["status"] == (
        "resolved"
    )

    assert data["response"]["action"] == (
        "password_reset"
    )

    assert analyzer.requests == [
        "My password has expired."
    ]

    assert knowledge.calls == [
        "My password has expired."
    ]

    assert password_tool.was_executed_for(
        "USR-API-002"
    )

    assert len(
        audit.get_all()
    ) > 0


# ----------------------------------------------------------------------
# Consent safety boundary
# ----------------------------------------------------------------------


def test_intent_api_does_not_execute_without_consent() -> None:
    (
        _service,
        _analyzer,
        intent_workflow,
        _knowledge,
        _audit,
        _itsm,
        password_tool,
    ) = create_self_healing_stack()

    app.dependency_overrides[
        get_intent_workflow_service
    ] = lambda: intent_workflow

    client = TestClient(app)

    response = client.post(
        "/api/v1/intent",
        json={
            "user_id": "USR-API-003",
            "employee_request": (
                "My password has expired."
            ),
            "consent_granted": False,
            "consent_source": (
                "not_required"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["response"]["status"] == (
        "confirmation_required"
    )

    assert password_tool.was_executed_for(
        "USR-API-003"
    ) is False