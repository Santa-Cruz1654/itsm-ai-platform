from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.enums import ConfidenceLevel, IntentType
from app.domain.intent import AIIntentAnalysis


class WorkflowRoute(StrEnum):
    """
    Deterministic downstream workflow categories.

    These values describe where the application should continue.
    They do not execute the workflow.
    """

    RAG = "rag"

    TICKET = "ticket"

    SERVICE_REQUEST = "service_request"

    AUTOMATION_REVIEW = "automation_review"

    CONFIRMATION_REQUIRED = "confirmation_required"

    ESCALATION = "escalation"


class RoutingReason(StrEnum):
    """
    Machine-readable explanation for why a route was selected.
    """

    KNOWLEDGE_QUESTION = "knowledge_question"

    INCIDENT = "incident"

    SERVICE_REQUEST = "service_request"

    AUTOMATABLE_ISSUE = "automatable_issue"

    UNKNOWN_INTENT = "unknown_intent"

    MEDIUM_CONFIDENCE = "medium_confidence"

    LOW_CONFIDENCE = "low_confidence"


@dataclass(frozen=True)
class IntentRoutingDecision:
    """
    Immutable result of deterministic intent routing.

    The decision describes what the application should do next.

    It does NOT perform that action.
    """

    route: WorkflowRoute
    reason: RoutingReason
    requires_confirmation: bool = False
    requires_human_escalation: bool = False


class IntentRouter:
    """
    Deterministic application service that converts a validated
    AIIntentAnalysis into a downstream workflow decision.

    Responsibilities:
        - apply confidence gating
        - apply supported-intent routing rules
        - produce a deterministic routing decision

    Does NOT:
        - call the LLM
        - call RAG
        - create tickets
        - execute automation
        - call ServiceNow
        - call tools
        - access repositories
        - make authorization decisions

    The router therefore remains deterministic and easily testable.
    """

    def route(
        self,
        analysis: AIIntentAnalysis,
    ) -> IntentRoutingDecision:
        """
        Convert validated AI analysis into a deterministic route.
        """

        # UNKNOWN is a safety classification, not an ambiguous supported
        # intent. It must never enter the generic confirmation path.
        if analysis.intent == IntentType.UNKNOWN:
            return IntentRoutingDecision(
                route=WorkflowRoute.ESCALATION,
                reason=RoutingReason.UNKNOWN_INTENT,
                requires_human_escalation=True,
            )

        if analysis.confidence == ConfidenceLevel.LOW:
            return IntentRoutingDecision(
                route=WorkflowRoute.ESCALATION,
                reason=RoutingReason.LOW_CONFIDENCE,
                requires_human_escalation=True,
            )

        if analysis.confidence == ConfidenceLevel.MEDIUM:
            return IntentRoutingDecision(
                route=WorkflowRoute.CONFIRMATION_REQUIRED,
                reason=RoutingReason.MEDIUM_CONFIDENCE,
                requires_confirmation=True,
            )

        return self._route_high_confidence(analysis)

    @staticmethod
    def _route_high_confidence(
        analysis: AIIntentAnalysis,
    ) -> IntentRoutingDecision:
        """
        Apply the supported-intent routing table after the confidence
        gate has passed.
        """

        if analysis.intent == IntentType.KNOWLEDGE_QUESTION:
            return IntentRoutingDecision(
                route=WorkflowRoute.RAG,
                reason=RoutingReason.KNOWLEDGE_QUESTION,
            )

        if analysis.intent == IntentType.INCIDENT:
            return IntentRoutingDecision(
                route=WorkflowRoute.TICKET,
                reason=RoutingReason.INCIDENT,
            )

        if analysis.intent == IntentType.SERVICE_REQUEST:
            return IntentRoutingDecision(
                route=WorkflowRoute.SERVICE_REQUEST,
                reason=RoutingReason.SERVICE_REQUEST,

            )

        if analysis.intent == IntentType.AUTOMATABLE_ISSUE:
            return IntentRoutingDecision(
                route=WorkflowRoute.AUTOMATION_REVIEW,
                reason=RoutingReason.AUTOMATABLE_ISSUE,
            )

        if analysis.intent == IntentType.UNKNOWN:
            return IntentRoutingDecision(
                route=WorkflowRoute.ESCALATION,
                reason=RoutingReason.UNKNOWN_INTENT,
                requires_human_escalation=True,
            )

        raise ValueError(
            f"Unsupported intent: {analysis.intent}"
        )