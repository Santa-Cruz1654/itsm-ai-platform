import pytest
from pydantic import ValidationError

from app.domain.enums import ConfidenceLevel, IntentType
from app.domain.intent import AIIntentAnalysis


def test_knowledge_question_intent_analysis():
    analysis = AIIntentAnalysis(
        intent=IntentType.KNOWLEDGE_QUESTION,
        category="email",
        subcategory="outlook",
        summary="Employee wants help troubleshooting Outlook synchronization.",
        confidence=ConfidenceLevel.HIGH,
    )

    assert analysis.intent == IntentType.KNOWLEDGE_QUESTION
    assert analysis.category == "email"
    assert analysis.subcategory == "outlook"
    assert analysis.automation_candidate is False


def test_incident_intent_analysis():
    analysis = AIIntentAnalysis(
        intent=IntentType.INCIDENT,
        category="network",
        subcategory="vpn",
        priority="P2",
        impact="medium",
        urgency="high",
        assignment_group="network_support",
        summary="Employee cannot connect to the corporate VPN.",
        confidence=ConfidenceLevel.HIGH,
    )

    assert analysis.intent == IntentType.INCIDENT
    assert analysis.priority == "P2"
    assert analysis.impact == "medium"
    assert analysis.urgency == "high"
    assert analysis.assignment_group == "network_support"


def test_service_request_intent_analysis():
    analysis = AIIntentAnalysis(
        intent=IntentType.SERVICE_REQUEST,
        category="software",
        subcategory="installation",
        summary="Employee requests installation of Visual Studio Code.",
        confidence=ConfidenceLevel.MEDIUM,
        software_name="Visual Studio Code",
    )

    assert analysis.intent == IntentType.SERVICE_REQUEST
    assert analysis.software_name == "Visual Studio Code"


def test_automatable_issue_intent_analysis():
    analysis = AIIntentAnalysis(
        intent=IntentType.AUTOMATABLE_ISSUE,
        category="account",
        subcategory="password",
        summary="Employee's password has expired.",
        confidence=ConfidenceLevel.HIGH,
        automation_candidate=True,
    )

    assert analysis.intent == IntentType.AUTOMATABLE_ISSUE
    assert analysis.automation_candidate is True


def test_unknown_intent_analysis():
    analysis = AIIntentAnalysis(
        intent=IntentType.UNKNOWN,
        summary="The request cannot be classified as a supported ITSM request.",
        confidence=ConfidenceLevel.LOW,
    )

    assert analysis.intent == IntentType.UNKNOWN
    assert analysis.confidence == ConfidenceLevel.LOW


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        AIIntentAnalysis(
            intent=IntentType.INCIDENT,
            summary="VPN is not working.",
            confidence=ConfidenceLevel.HIGH,
            execute_command="restart-vpn",
        )


def test_empty_summary_is_rejected():
    with pytest.raises(ValidationError):
        AIIntentAnalysis(
            intent=IntentType.INCIDENT,
            summary="",
            confidence=ConfidenceLevel.HIGH,
        )


def test_whitespace_only_summary_is_rejected():
    with pytest.raises(ValidationError):
        AIIntentAnalysis(
            intent=IntentType.INCIDENT,
            summary="   ",
            confidence=ConfidenceLevel.HIGH,
        )


def test_invalid_intent_is_rejected():
    with pytest.raises(ValidationError):
        AIIntentAnalysis(
            intent="random_workflow",
            summary="VPN is not working.",
            confidence=ConfidenceLevel.HIGH,
        )


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValidationError):
        AIIntentAnalysis(
            intent=IntentType.INCIDENT,
            summary="VPN is not working.",
            confidence="certain",
        )


def test_optional_string_fields_reject_empty_values():
    with pytest.raises(ValidationError):
        AIIntentAnalysis(
            intent=IntentType.INCIDENT,
            category="",
            summary="VPN is not working.",
            confidence=ConfidenceLevel.HIGH,
        )


def test_optional_fields_can_be_none():
    analysis = AIIntentAnalysis(
        intent=IntentType.UNKNOWN,
        category=None,
        subcategory=None,
        priority=None,
        impact=None,
        urgency=None,
        assignment_group=None,
        summary="Unsupported request.",
        confidence=ConfidenceLevel.LOW,
        software_name=None,
    )

    assert analysis.category is None
    assert analysis.subcategory is None
    assert analysis.software_name is None