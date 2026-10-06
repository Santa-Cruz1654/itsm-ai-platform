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

    The result contains:

        - validated AI analysis
        - deterministic routing decision
        - downstream workflow response
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
    7. Handle explicit human escalation requests.

    This service does NOT:

    - classify intent
    - call the LLM directly
    - execute tools
    - access repositories directly
    - implement ServiceNow
    - implement provisioning infrastructure
    - decide whether an arbitrary action is safe

    IMPORTANT SAFETY BOUNDARY

    An UNKNOWN or low-confidence request must never receive an
    invented answer or automatically execute a workflow.

    Escalation ticket creation requires:

        1. the workflow to be in the ESCALATION state
        2. a valid user identity
        3. an explicitly requested escalation ticket
        4. the existing TicketService boundary

    The LLM never creates a ticket directly.
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
        self._intent_analyzer = (
            intent_analyzer
        )

        self._intent_router = (
            intent_router
        )

        self._knowledge_retrieval_service = (
            knowledge_retrieval_service
        )

        self._ticket_service = (
            ticket_service
        )

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

        create_escalation_ticket is intentionally separate from
        consent_granted.

        Consent is used by controlled automation workflows.

        Escalation ticket creation is an explicit user-requested
        workflow action and must never be inferred from AI confidence.
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

        IntentRouter owns the routing decision.

        IntentWorkflowService only composes the selected workflow
        with the appropriate existing application service.
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
        """
        Retrieve enterprise knowledge for a knowledge question.

        Final grounded answer generation remains inside the dedicated
        KnowledgeAnswerService / /knowledge/ask flow.

        This workflow does not invent an answer when retrieval is
        unavailable.
        """

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
    # Escalation
    # ------------------------------------------------------------------

    def _handle_escalation(
        self,
        *,
        employee_request: str,
        user_id: str | None,
        analysis: AIIntentAnalysis,
        create_escalation_ticket: bool,
    ) -> dict[str, Any]:
        """
        Handle UNKNOWN / low-confidence escalation.

        SAFETY RULE:

            No generated answer is returned.

        The employee is explicitly informed that the system cannot
        answer reliably.

        A ticket is created only when:

            create_escalation_ticket=True

        This prevents AI uncertainty from silently creating ITSM
        records or triggering downstream actions.
        """

        message = self._build_escalation_message(
            analysis
        )

        # --------------------------------------------------------------
        # No explicit ticket request.
        # --------------------------------------------------------------

        if not create_escalation_ticket:
            return {
                "status": "escalation_required",
                "message": message,
                "requires_human_escalation": True,
                "can_create_ticket": (
                    self._ticket_service is not None
                    and user_id is not None
                    and bool(user_id.strip())
                ),
                "ticket_requested": False,
                "ticket": None,
            }

        # --------------------------------------------------------------
        # Explicit ticket request requires TicketService.
        # --------------------------------------------------------------

        if self._ticket_service is None:
            return {
                "status": (
                    "ticket_creation_required"
                ),
                "message": (
                    f"{message} "
                    "An IT support ticket cannot be created "
                    "because the ticket service is not configured."
                ),
                "requires_human_escalation": True,
                "can_create_ticket": False,
                "ticket_requested": True,
                "ticket": None,
            }

        # --------------------------------------------------------------
        # Explicit ticket request requires user identity.
        # --------------------------------------------------------------

        if user_id is None or not user_id.strip():
            return {
                "status": (
                    "user_context_required"
                ),
                "message": (
                    f"{message} "
                    "A user identity is required before "
                    "an IT support ticket can be created."
                ),
                "requires_human_escalation": True,
                "can_create_ticket": False,
                "ticket_requested": True,
                "ticket": None,
            }

        # --------------------------------------------------------------
        # Create the escalation incident through TicketService.
        # --------------------------------------------------------------

        ticket = self._ticket_service.create_ticket(
            ticket_type=TicketType.INCIDENT,
            title=(
                "AI escalation: "
                f"{analysis.summary}"
            ),
            description=(
                "AI could not provide a reliable "
                "answer or supported workflow.\n\n"
                "Original employee request:\n"
                f"{employee_request}\n\n"
                "Escalation reason:\n"
                f"{self._escalation_reason(analysis)}\n\n"
                "No unsupported resolution was generated."
            ),
            user_id=user_id,
        )

        return {
            "status": (
                "escalation_ticket_created"
            ),
            "message": (
                "I could not provide a reliable answer "
                "from the supported enterprise ITSM "
                "knowledge and workflows. "
                "I created an IT support ticket for "
                "further assistance."
            ),
            "requires_human_escalation": True,
            "can_create_ticket": True,
            "ticket_requested": True,
            "ticket": self._ticket_reference(
                ticket
            ),
        }

    @staticmethod
    def _build_escalation_message(
        analysis: AIIntentAnalysis,
    ) -> str:
        """
        Build a deterministic employee-facing escalation message.

        This method deliberately does not ask the LLM to explain
        the unsupported topic.
        """

        if analysis.intent.value == "unknown":
            return (
                "I couldn't find sufficient approved "
                "enterprise knowledge or a supported ITSM "
                "workflow to answer this reliably. "
                "I won't guess or provide an unsupported "
                "answer. I can create an IT support ticket "
                "for further assistance."
            )

        return (
            "I couldn't classify this request with "
            "enough confidence to answer or route it "
            "reliably. I won't guess or provide an "
            "unsupported answer. I can create an IT "
            "support ticket for further assistance."
        )

    @staticmethod
    def _escalation_reason(
        analysis: AIIntentAnalysis,
    ) -> str:
        if analysis.intent.value == "unknown":
            return (
                "The request was classified as "
                "UNKNOWN / UNSUPPORTED."
            )

        if analysis.confidence.value == "low":
            return (
                "The intent classification confidence "
                "was LOW."
            )

        return (
            "The request requires human assistance "
            "because the AI workflow could not safely "
            "continue."
        )

    @staticmethod
    def _ticket_reference(
        ticket: Any,
    ) -> dict[str, Any]:
        """
        Convert the internal Ticket object into a stable employee/API
        escalation reference.

        Supports both the real Pydantic Ticket model and lightweight
        test doubles.
        """

        if hasattr(ticket, "model_dump"):
            data = ticket.model_dump(
                mode="json"
            )
        elif isinstance(ticket, dict):
            data = dict(ticket)
        else:
            data = {
                "ticket_id": getattr(
                    ticket,
                    "ticket_id",
                    None,
                ),
                "type": getattr(
                    ticket,
                    "type",
                    None,
                ),
                "status": getattr(
                    ticket,
                    "status",
                    None,
                ),
                "external_system": getattr(
                    ticket,
                    "external_system",
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
                "external_sync_status": getattr(
                    ticket,
                    "external_sync_status",
                    None,
                ),
            }

        return {
            "ticket_id": data.get(
                "ticket_id"
            ),
            "type": data.get(
                "type"
            ),
            "status": data.get(
                "status"
            ),
            "external_system": data.get(
                "external_system"
            ),
            "external_ticket_id": data.get(
                "external_ticket_id"
            ),
            "external_ticket_number": data.get(
                "external_ticket_number"
            ),
            "external_sync_status": data.get(
                "external_sync_status"
            ),
        }