from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.intent.intent_analyzer import (
    IntentAnalyzer,
)
from app.application.intent.intent_router import (
    IntentRouter,
    IntentRoutingDecision,
    WorkflowRoute,
)
from app.application.knowledge.retrieval_service import (
    KnowledgeRetrievalService,
)
from app.application.self_healing_service import (
    SelfHealingWorkflowService,
)
from app.application.software_provisioning_service import (
    SoftwareProvisioningService,
)
from app.application.ticket_service import (
    TicketService,
)
from app.domain.enums import (
    ConsentSource,
    TicketType,
)
from app.domain.intent import (
    AIIntentAnalysis,
)


@dataclass(frozen=True)
class IntentWorkflowResult:
    """
    Result produced by the AI-assisted ITSM workflow.
    """

    analysis: AIIntentAnalysis
    decision: IntentRoutingDecision
    response: Any


class IntentWorkflowService:
    """
    Application-level orchestrator for AI-assisted ITSM workflows.

    Responsibilities:

        1. Analyze the employee request.
        2. Apply deterministic intent routing.
        3. Delegate executable routes to existing application services.
        4. Stop safely for confirmation, escalation, or automation review.
        5. Delegate automation candidates to self-healing.
        6. Delegate software requests to software provisioning.

    This service does NOT:

        - classify intent
        - call the LLM directly
        - execute tools
        - access repositories directly
        - implement ServiceNow
        - implement provisioning infrastructure
    """

    def __init__(
        self,
        *,
        intent_analyzer: IntentAnalyzer,
        intent_router: IntentRouter,
        knowledge_retrieval_service: (
            KnowledgeRetrievalService | None
        ) = None,
        ticket_service: TicketService | None = None,
        self_healing_service: (
            SelfHealingWorkflowService | None
        ) = None,
        software_provisioning_service: (
            SoftwareProvisioningService | None
        ) = None,
    ) -> None:
        self._intent_analyzer = intent_analyzer

        self._intent_router = intent_router

        self._knowledge_retrieval_service = (
            knowledge_retrieval_service
        )

        self._ticket_service = ticket_service

        self._self_healing_service = (
            self_healing_service
        )

        self._software_provisioning_service = (
            software_provisioning_service
        )

    # ------------------------------------------------------------------
    # Public application use case
    # ------------------------------------------------------------------

    def handle(
        self,
        employee_request: str,
        *,
        user_id: str | None = None,
        consent_granted: bool = False,
        consent_source: ConsentSource = (
            ConsentSource.NOT_REQUIRED
        ),
        create_escalation_ticket: bool = False,
    ) -> IntentWorkflowResult:
        """
        Analyze and route an employee request.

        create_escalation_ticket is intentionally False by default.

        UNKNOWN or LOW-confidence requests must never create an ITSM
        ticket implicitly.

        A ticket is created only when the caller explicitly requests
        escalation ticket creation.
        """

        employee_request = (
            employee_request.strip()
        )

        if not employee_request:
            raise ValueError(
                "Employee request cannot be empty."
            )

        analysis = (
            self._intent_analyzer.analyze(
                employee_request,
            )
        )

        decision = (
            self._intent_router.route(
                analysis,
            )
        )

        response = self._dispatch(
            employee_request=employee_request,
            user_id=user_id,
            analysis=analysis,
            decision=decision,
            consent_granted=consent_granted,
            consent_source=consent_source,
            create_escalation_ticket=(
                create_escalation_ticket
            ),
        )

        return IntentWorkflowResult(
            analysis=analysis,
            decision=decision,
            response=response,
        )

    # ------------------------------------------------------------------
    # Routing dispatch
    # ------------------------------------------------------------------

    def _dispatch(
        self,
        *,
        employee_request: str,
        user_id: str | None,
        analysis: AIIntentAnalysis,
        decision: IntentRoutingDecision,
        consent_granted: bool,
        consent_source: ConsentSource,
        create_escalation_ticket: bool,
    ) -> Any:
        """
        Dispatch an already-determined route.
        """

        if decision.route == WorkflowRoute.RAG:
            return self._handle_knowledge_question(
                employee_request=employee_request,
                analysis=analysis,
            )

        if decision.route == WorkflowRoute.TICKET:
            return self._handle_incident(
                employee_request=employee_request,
                user_id=user_id,
                analysis=analysis,
            )

        if decision.route == WorkflowRoute.SERVICE_REQUEST:
            return self._handle_service_request(
                employee_request=employee_request,
                user_id=user_id,
                analysis=analysis,
            )

        if decision.route == WorkflowRoute.AUTOMATION_REVIEW:
            return self._handle_automation_review(
                employee_request=employee_request,
                user_id=user_id,
                analysis=analysis,
                consent_granted=consent_granted,
                consent_source=consent_source,
            )

        if decision.route == WorkflowRoute.CONFIRMATION_REQUIRED:
            return self._confirmation_response(
                analysis,
            )

        if decision.route == WorkflowRoute.ESCALATION:
            return self._handle_escalation(
                employee_request=employee_request,
                user_id=user_id,
                analysis=analysis,
                decision=decision,
                create_escalation_ticket=(
                    create_escalation_ticket
                ),
            )

        raise RuntimeError(
            f"Unsupported workflow route: {decision.route}"
        )

    # ------------------------------------------------------------------
    # Knowledge workflow
    # ------------------------------------------------------------------

    def _handle_knowledge_question(
        self,
        *,
        employee_request: str,
        analysis: AIIntentAnalysis,
    ) -> Any:
        if (
            self._knowledge_retrieval_service
            is None
        ):
            return {
                "status": (
                    "knowledge_retrieval_required"
                ),
                "message": (
                    "The request was classified as "
                    "a knowledge question, but the "
                    "knowledge retrieval service is "
                    "not configured."
                ),
            }

        filters: dict[str, Any] = {}

        if analysis.category:
            filters["category"] = (
                analysis.category
            )

        if analysis.subcategory:
            filters["subcategory"] = (
                analysis.subcategory
            )

        return (
            self._knowledge_retrieval_service.search(
                employee_request,
                mode="hybrid",
                limit=5,
                filters=filters or None,
            )
        )

    # ------------------------------------------------------------------
    # Incident workflow
    # ------------------------------------------------------------------

    def _handle_incident(
        self,
        *,
        employee_request: str,
        user_id: str | None,
        analysis: AIIntentAnalysis,
    ) -> Any:
        if self._ticket_service is None:
            return {
                "status": (
                    "ticket_creation_required"
                ),
                "message": (
                    "The request was classified as "
                    "an incident, but the ticket service "
                    "is not configured."
                ),
            }

        if user_id is None or not user_id.strip():
            return {
                "status": (
                    "user_context_required"
                ),
                "message": (
                    "A user identity is required before "
                    "an incident can be created."
                ),
            }

        return self._ticket_service.create_ticket(
            ticket_type=TicketType.INCIDENT,
            title=analysis.summary,
            description=employee_request,
            user_id=user_id,
        )

    # ------------------------------------------------------------------
    # Service request / software provisioning
    # ------------------------------------------------------------------

    def _handle_service_request(
        self,
        *,
        employee_request: str,
        user_id: str | None,
        analysis: AIIntentAnalysis,
    ) -> Any:
        """
        Handle service requests.

        If the AI identified a concrete software product,
        route into the controlled software provisioning workflow.

        Otherwise preserve the existing generic service-request
        behavior through TicketService.
        """

        if user_id is None or not user_id.strip():
            return {
                "status": (
                    "user_context_required"
                ),
                "message": (
                    "A user identity is required before "
                    "a service request can be created."
                ),
            }

        # --------------------------------------------------------------
        # Software provisioning
        # --------------------------------------------------------------

        if analysis.software_name:
            if (
                self._software_provisioning_service
                is None
            ):
                return {
                    "status": (
                        "software_provisioning_required"
                    ),
                    "message": (
                        "The request contains a software "
                        "installation request, but the "
                        "software provisioning service is "
                        "not configured."
                    ),
                    "software_name": (
                        analysis.software_name
                    ),
                }

            return (
                self._software_provisioning_service
                .request_installation(
                    user_id=user_id,
                    software_name=(
                        analysis.software_name
                    ),
                    employee_request=(
                        employee_request
                    ),
                )
            )

        # --------------------------------------------------------------
        # Existing generic service-request behavior
        # --------------------------------------------------------------

        if self._ticket_service is None:
            return {
                "status": (
                    "request_creation_required"
                ),
                "message": (
                    "The request was classified as "
                    "a service request, but the ticket "
                    "service is not configured."
                ),
            }

        return self._ticket_service.create_ticket(
            ticket_type=TicketType.REQUEST,
            title=analysis.summary,
            description=employee_request,
            user_id=user_id,
        )

    # ------------------------------------------------------------------
    # Automation / self-healing
    # ------------------------------------------------------------------

    def _handle_automation_review(
        self,
        *,
        employee_request: str,
        user_id: str | None,
        analysis: AIIntentAnalysis,
        consent_granted: bool,
        consent_source: ConsentSource,
    ) -> Any:
        if self._self_healing_service is None:
            return {
                "status": (
                    "automation_review_required"
                ),
                "message": (
                    "The request appears suitable for "
                    "a controlled automation workflow and "
                    "requires policy and action resolution "
                    "before execution."
                ),
                "summary": analysis.summary,
                "category": analysis.category,
                "subcategory": analysis.subcategory,
                "automation_candidate": (
                    analysis.automation_candidate
                ),
            }

        if user_id is None or not user_id.strip():
            return {
                "status": (
                    "user_context_required"
                ),
                "message": (
                    "A user identity is required before "
                    "self-healing can be attempted."
                ),
            }

        return self._self_healing_service.handle(
            employee_request=employee_request,
            user_id=user_id,
            analysis=analysis,
            consent_granted=consent_granted,
            consent_source=consent_source,
        )

    # ------------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------------

    @staticmethod
    def _confirmation_response(
        analysis: AIIntentAnalysis,
    ) -> dict[str, str]:
        return {
            "status": (
                "confirmation_required"
            ),
            "message": (
                "I need your confirmation before "
                "continuing. I believe your request is: "
                f"{analysis.summary}"
            ),
        }

    # ------------------------------------------------------------------
    # Phase 10 - Unknown / unsupported escalation
    # ------------------------------------------------------------------

    def _handle_escalation(
        self,
        *,
        employee_request: str,
        user_id: str | None,
        analysis: AIIntentAnalysis,
        decision: IntentRoutingDecision,
        create_escalation_ticket: bool,
    ) -> dict[str, Any]:
        """
        Handle UNKNOWN and LOW-confidence requests.

        Safety rules:

            1. Never generate an unsupported answer.
            2. Never invoke RAG from the UNKNOWN route.
            3. Never create a ticket implicitly.
            4. Create an incident only when explicitly requested.
            5. Require user identity for ticket creation.
            6. Explicitly mark the created ticket as ESCALATED.
        """

        if decision.reason == "unknown_intent":
            message = (
                "I couldn't find sufficient approved "
                "knowledge-base information to answer "
                "this reliably. I can create an IT support "
                "ticket for further assistance."
            )

        elif decision.reason == "low_confidence":
            message = (
                "I couldn't determine your request "
                "reliably enough to continue safely. "
                "I can create an IT support ticket for "
                "further assistance."
            )

        else:
            message = (
                "I couldn't map your request to a "
                "supported ITSM workflow reliably. "
                "I can create an IT support ticket for "
                "further assistance."
            )

        response: dict[str, Any] = {
            "status": "escalation_required",
            "message": message,
            "ticket_created": False,
        }

        # --------------------------------------------------------------
        # Important safety boundary:
        #
        # UNKNOWN does NOT automatically create a ticket.
        # --------------------------------------------------------------

        if not create_escalation_ticket:
            return response

        # --------------------------------------------------------------
        # Explicit escalation requested.
        # --------------------------------------------------------------

        if self._ticket_service is None:
            response.update(
                {
                    "status": (
                        "escalation_ticket_unavailable"
                    ),
                    "message": (
                        f"{message} "
                        "However, the ITSM ticket service "
                        "is currently unavailable."
                    ),
                }
            )

            return response

        if user_id is None or not user_id.strip():
            response.update(
                {
                    "status": (
                        "user_context_required"
                    ),
                    "message": (
                        f"{message} "
                        "A user identity is required before "
                        "the escalation ticket can be created."
                    ),
                }
            )

            return response

        # --------------------------------------------------------------
        # First create the internal/external ticket.
        #
        # create_ticket() intentionally creates tickets as OPEN.
        # Escalation is a separate business operation.
        # --------------------------------------------------------------

        ticket = self._ticket_service.create_ticket(
            ticket_type=TicketType.INCIDENT,
            title=(
                f"AI escalation: "
                f"{analysis.summary}"
            ),
            description=(
                "AI escalation request.\n\n"
                f"Original employee request:\n"
                f"{employee_request}\n\n"
                f"Escalation reason:\n"
                f"{decision.reason}\n\n"
                f"AI confidence:\n"
                f"{analysis.confidence.value}"
            ),
            user_id=user_id,
        )

        # --------------------------------------------------------------
        # Explicitly transition the newly-created ticket to ESCALATED.
        #
        # This keeps normal incident creation OPEN while ensuring that
        # an explicit AI escalation is represented correctly in both
        # the ticket state and dashboard metrics.
        # --------------------------------------------------------------

        ticket = self._ticket_service.escalate_ticket(
            ticket.ticket_id
        )

        response.update(
            {
                "status": "escalated",
                "message": (
                    "I couldn't find sufficient approved "
                    "knowledge-base information to answer "
                    "this reliably. Your IT support ticket "
                    "has been created for further assistance."
                ),
                "ticket_created": True,
                "ticket_id": getattr(
                    ticket,
                    "ticket_id",
                    None,
                ),
                "external_ticket_id": getattr(
                    ticket,
                    "external_ticket_id",
                    None,
                ),
                "external_ticket_number": getattr(
                    ticket,
                    "external_ticket_number",
                    None,
                ),
            }
        )

        return response