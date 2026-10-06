import pytest
from pydantic import ValidationError

from app.application.intent.intent_analyzer import (
    IntentAnalysisError,
    IntentAnalyzer,
    IntentAnalyzerConfig,
)
from app.domain.enums import ConfidenceLevel, IntentType


class FakeLLMProvider:
    def __init__(
        self,
        responses: list[str],
    ) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def generate(
        self,
        prompt: str,
    ) -> str:
        self.prompts.append(prompt)

        if not self.responses:
            raise AssertionError(
                "FakeLLMProvider has no response left"
            )

        return self.responses.pop(0)


def _valid_incident_response() -> str:
    return """
    {
      "intent": "incident",
      "category": "network",
      "subcategory": "vpn",
      "priority": "P2",
      "impact": "medium",
      "urgency": "high",
      "assignment_group": "network_support",
      "summary": "Employee cannot connect to the corporate VPN.",
      "confidence": "high",
      "automation_candidate": false,
      "software_name": null
    }
    """


def test_analyzer_returns_valid_incident_analysis():
    provider = FakeLLMProvider(
        [_valid_incident_response()]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    result = analyzer.analyze(
        "My VPN is not working."
    )

    assert result.intent == IntentType.INCIDENT
    assert result.category == "network"
    assert result.subcategory == "vpn"
    assert result.priority == "P2"
    assert result.confidence == ConfidenceLevel.HIGH
    assert result.automation_candidate is False


def test_analyzer_returns_knowledge_question():
    provider = FakeLLMProvider(
        [
            """
            {
              "intent": "knowledge_question",
              "category": "email",
              "subcategory": "outlook",
              "priority": null,
              "impact": null,
              "urgency": null,
              "assignment_group": null,
              "summary": "Employee wants help fixing Outlook synchronization.",
              "confidence": "high",
              "automation_candidate": false,
              "software_name": "Microsoft Outlook"
            }
            """
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    result = analyzer.analyze(
        "How do I fix Outlook synchronization?"
    )

    assert result.intent == IntentType.KNOWLEDGE_QUESTION
    assert result.software_name == "Microsoft Outlook"


def test_analyzer_returns_service_request():
    provider = FakeLLMProvider(
        [
            """
            {
              "intent": "service_request",
              "category": "software",
              "subcategory": "installation",
              "priority": null,
              "impact": null,
              "urgency": null,
              "assignment_group": "desktop_support",
              "summary": "Employee requests Visual Studio Code installation.",
              "confidence": "high",
              "automation_candidate": false,
              "software_name": "Visual Studio Code"
            }
            """
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    result = analyzer.analyze(
        "Please install Visual Studio Code."
    )

    assert result.intent == IntentType.SERVICE_REQUEST
    assert result.software_name == "Visual Studio Code"


def test_analyzer_returns_automatable_issue():
    provider = FakeLLMProvider(
        [
            """
            {
              "intent": "automatable_issue",
              "category": "account",
              "subcategory": "password",
              "priority": null,
              "impact": null,
              "urgency": null,
              "assignment_group": "identity_support",
              "summary": "Employee password has expired.",
              "confidence": "high",
              "automation_candidate": true,
              "software_name": null
            }
            """
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    result = analyzer.analyze(
        "My password has expired."
    )

    assert result.intent == IntentType.AUTOMATABLE_ISSUE
    assert result.automation_candidate is True


def test_analyzer_returns_unknown_for_unsupported_request():
    provider = FakeLLMProvider(
        [
            """
            {
              "intent": "unknown",
              "category": null,
              "subcategory": null,
              "priority": null,
              "impact": null,
              "urgency": null,
              "assignment_group": null,
              "summary": "Request is outside supported enterprise ITSM scope.",
              "confidence": "high",
              "automation_candidate": false,
              "software_name": null
            }
            """
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    result = analyzer.analyze(
        "How do I repair my refrigerator?"
    )

    assert result.intent == IntentType.UNKNOWN


def test_analyzer_accepts_json_inside_markdown_fence():
    provider = FakeLLMProvider(
        [
            f"""
            ```json
            {_valid_incident_response()}
            ```
            """
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    result = analyzer.analyze(
        "VPN is not working."
    )

    assert result.intent == IntentType.INCIDENT


def test_analyzer_accepts_json_with_surrounding_text():
    provider = FakeLLMProvider(
        [
            f"""
            Here is the classification:

            {_valid_incident_response()}

            End of classification.
            """
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    result = analyzer.analyze(
        "VPN is not working."
    )

    assert result.intent == IntentType.INCIDENT


def test_analyzer_rejects_invalid_intent_after_retry():
    provider = FakeLLMProvider(
        [
            """
            {
              "intent": "printer_problem",
              "category": "hardware",
              "subcategory": "printer",
              "priority": null,
              "impact": null,
              "urgency": null,
              "assignment_group": null,
              "summary": "Printer is not working.",
              "confidence": "high",
              "automation_candidate": false,
              "software_name": null
            }
            """,
            """
            {
              "intent": "incident",
              "category": "hardware",
              "subcategory": "printer",
              "priority": "P2",
              "impact": "medium",
              "urgency": "high",
              "assignment_group": "desktop_support",
              "summary": "Employee reports a printer failure.",
              "confidence": "high",
              "automation_candidate": false,
              "software_name": null
            }
            """,
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    result = analyzer.analyze(
        "My office printer is not working."
    )

    assert result.intent == IntentType.INCIDENT
    assert len(provider.prompts) == 2


def test_analyzer_rejects_extra_fields_after_retry():
    provider = FakeLLMProvider(
        [
            """
            {
              "intent": "incident",
              "category": "network",
              "subcategory": "vpn",
              "priority": "P2",
              "impact": "medium",
              "urgency": "high",
              "assignment_group": "network_support",
              "summary": "VPN is unavailable.",
              "confidence": "high",
              "automation_candidate": false,
              "software_name": null,
              "execute_command": "restart_vpn"
            }
            """,
            _valid_incident_response(),
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    result = analyzer.analyze(
        "My VPN is not working."
    )

    assert result.intent == IntentType.INCIDENT
    assert len(provider.prompts) == 2


def test_analyzer_retries_malformed_json():
    provider = FakeLLMProvider(
        [
            '{"intent": "incident",',
            _valid_incident_response(),
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    result = analyzer.analyze(
        "My VPN is not working."
    )

    assert result.intent == IntentType.INCIDENT
    assert len(provider.prompts) == 2


def test_analyzer_raises_after_retry_exhaustion():
    provider = FakeLLMProvider(
        [
            "not json",
            "still not json",
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    with pytest.raises(IntentAnalysisError):
        analyzer.analyze(
            "My VPN is not working."
        )

    assert len(provider.prompts) == 2


def test_analyzer_rejects_empty_request():
    provider = FakeLLMProvider(
        [_valid_incident_response()]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        analyzer.analyze("   ")

    assert provider.prompts == []


def test_analyzer_rejects_non_string_request():
    provider = FakeLLMProvider(
        [_valid_incident_response()]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    with pytest.raises(ValueError, match="must be a string"):
        analyzer.analyze(None)  # type: ignore[arg-type]

    assert provider.prompts == []


def test_analyzer_rejects_empty_llm_response():
    provider = FakeLLMProvider(
        [
            "",
            _valid_incident_response(),
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    result = analyzer.analyze(
        "My VPN is not working."
    )

    assert result.intent == IntentType.INCIDENT
    assert len(provider.prompts) == 2


def test_analyzer_rejects_non_string_llm_response():
    class InvalidProvider:
        def generate(
            self,
            prompt: str,
        ) -> object:
            return {"intent": "incident"}

    analyzer = IntentAnalyzer(
        llm_provider=InvalidProvider(),  # type: ignore[arg-type]
    )

    with pytest.raises(IntentAnalysisError):
        analyzer.analyze(
            "My VPN is not working."
        )


def test_retry_prompt_contains_original_request():
    provider = FakeLLMProvider(
        [
            "invalid",
            _valid_incident_response(),
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
    )

    analyzer.analyze(
        "My corporate VPN stopped working."
    )

    assert len(provider.prompts) == 2
    assert (
        "My corporate VPN stopped working."
        in provider.prompts[1]
    )


def test_custom_retry_configuration():
    provider = FakeLLMProvider(
        [
            "invalid",
            "invalid",
            _valid_incident_response(),
        ]
    )

    analyzer = IntentAnalyzer(
        llm_provider=provider,
        config=IntentAnalyzerConfig(
            max_retries=2,
        ),
    )

    result = analyzer.analyze(
        "My VPN is not working."
    )

    assert result.intent == IntentType.INCIDENT
    assert len(provider.prompts) == 3


def test_negative_retry_configuration_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        IntentAnalyzerConfig(
            max_retries=-1,
        )