import pytest

from app.application.intent.intent_router import (
    IntentRouter,
    RoutingReason,
    WorkflowRoute,
)
from app.domain.enums import ConfidenceLevel, IntentType
from app.domain.intent import AIIntentAnalysis


@pytest.fixture
def router() -> IntentRouter:
    return IntentRouter()


def create_analysis(
    *,
    intent: IntentType,
    confidence: ConfidenceLevel,
    automation_candidate: bool = False,
) -> AIIntentAnalysis:
    return AIIntentAnalysis(
        intent=intent,
        category="test",
        subcategory="test",
        priority=None,
        impact=None,
        urgency=None,
        assignment_group=None,
        summary="Test ITSM request.",
        confidence=confidence,
        automation_candidate=automation_candidate,
        software_name=None,
    )


# ---------------------------------------------------------------------------
# HIGH CONFIDENCE
# ---------------------------------------------------------------------------


def test_high_confidence_knowledge_question_routes_to_rag(
    router: IntentRouter,
) -> None:
    analysis = create_analysis(
        intent=IntentType.KNOWLEDGE_QUESTION,
        confidence=ConfidenceLevel.HIGH,
    )

    decision = router.route(analysis)

    assert decision.route == WorkflowRoute.RAG
    assert decision.reason == RoutingReason.KNOWLEDGE_QUESTION
    assert decision.requires_confirmation is False
    assert decision.requires_human_escalation is False


def test_high_confidence_incident_routes_to_ticket(
    router: IntentRouter,
) -> None:
    analysis = create_analysis(
        intent=IntentType.INCIDENT,
        confidence=ConfidenceLevel.HIGH,
    )

    decision = router.route(analysis)

    assert decision.route == WorkflowRoute.TICKET
    assert decision.reason == RoutingReason.INCIDENT
    assert decision.requires_confirmation is False
    assert decision.requires_human_escalation is False


def test_high_confidence_service_request_routes_to_service_request(
    router: IntentRouter,
) -> None:
    analysis = create_analysis(
        intent=IntentType.SERVICE_REQUEST,
        confidence=ConfidenceLevel.HIGH,
    )

    decision = router.route(analysis)

    assert decision.route == WorkflowRoute.SERVICE_REQUEST
    assert decision.reason == RoutingReason.SERVICE_REQUEST
    assert decision.requires_confirmation is False
    assert decision.requires_human_escalation is False


def test_high_confidence_automatable_issue_routes_to_review(
    router: IntentRouter,
) -> None:
    analysis = create_analysis(
        intent=IntentType.AUTOMATABLE_ISSUE,
        confidence=ConfidenceLevel.HIGH,
        automation_candidate=True,
    )

    decision = router.route(analysis)

    assert decision.route == WorkflowRoute.AUTOMATION_REVIEW
    assert decision.reason == RoutingReason.AUTOMATABLE_ISSUE
    assert decision.requires_confirmation is False
    assert decision.requires_human_escalation is False


def test_high_confidence_unknown_routes_to_escalation(
    router: IntentRouter,
) -> None:
    analysis = create_analysis(
        intent=IntentType.UNKNOWN,
        confidence=ConfidenceLevel.HIGH,
    )

    decision = router.route(analysis)

    assert decision.route == WorkflowRoute.ESCALATION
    assert decision.reason == RoutingReason.UNKNOWN_INTENT
    assert decision.requires_confirmation is False
    assert decision.requires_human_escalation is True


# ---------------------------------------------------------------------------
# MEDIUM CONFIDENCE
# ---------------------------------------------------------------------------


def test_medium_confidence_unknown_routes_to_escalation(
    router: IntentRouter,
) -> None:
    analysis = create_analysis(
        intent=IntentType.UNKNOWN,
        confidence=ConfidenceLevel.MEDIUM,
    )

    decision = router.route(analysis)

    assert decision.route == WorkflowRoute.ESCALATION
    assert decision.reason == RoutingReason.UNKNOWN_INTENT
    assert decision.requires_confirmation is False
    assert decision.requires_human_escalation is True


@pytest.mark.parametrize(
    "intent",
    [
        IntentType.KNOWLEDGE_QUESTION,
        IntentType.INCIDENT,
        IntentType.SERVICE_REQUEST,
        IntentType.AUTOMATABLE_ISSUE,
    ],
)
def test_medium_confidence_requires_confirmation(
    router: IntentRouter,
    intent: IntentType,
) -> None:
    analysis = create_analysis(
        intent=intent,
        confidence=ConfidenceLevel.MEDIUM,
    )

    decision = router.route(analysis)

    assert decision.route == WorkflowRoute.CONFIRMATION_REQUIRED
    assert decision.reason == RoutingReason.MEDIUM_CONFIDENCE
    assert decision.requires_confirmation is True
    assert decision.requires_human_escalation is False


# ---------------------------------------------------------------------------
# LOW CONFIDENCE
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "intent",
    [
        IntentType.KNOWLEDGE_QUESTION,
        IntentType.INCIDENT,
        IntentType.SERVICE_REQUEST,
        IntentType.AUTOMATABLE_ISSUE,
    ],
)
def test_low_confidence_requires_human_escalation(
    router: IntentRouter,
    intent: IntentType,
) -> None:
    analysis = create_analysis(
        intent=intent,
        confidence=ConfidenceLevel.LOW,
    )

    decision = router.route(analysis)

    assert decision.route == WorkflowRoute.ESCALATION
    assert decision.reason == RoutingReason.LOW_CONFIDENCE
    assert decision.requires_confirmation is False
    assert decision.requires_human_escalation is True


# ---------------------------------------------------------------------------
# SAFETY / DETERMINISM
# ---------------------------------------------------------------------------


def test_automatable_issue_never_directly_executes(
    router: IntentRouter,
) -> None:
    analysis = create_analysis(
        intent=IntentType.AUTOMATABLE_ISSUE,
        confidence=ConfidenceLevel.HIGH,
        automation_candidate=True,
    )

    decision = router.route(analysis)

    assert decision.route == WorkflowRoute.AUTOMATION_REVIEW
    assert decision.route != WorkflowRoute.TICKET


def test_router_does_not_modify_analysis(
    router: IntentRouter,
) -> None:
    analysis = create_analysis(
        intent=IntentType.INCIDENT,
        confidence=ConfidenceLevel.HIGH,
    )

    original_dump = analysis.model_dump()

    router.route(analysis)

    assert analysis.model_dump() == original_dump


def test_same_analysis_always_produces_same_decision(
    router: IntentRouter,
) -> None:
    analysis = create_analysis(
        intent=IntentType.INCIDENT,
        confidence=ConfidenceLevel.HIGH,
    )

    first = router.route(analysis)
    second = router.route(analysis)

    assert first == second