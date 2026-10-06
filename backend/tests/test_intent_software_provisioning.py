from __future__ import annotations

from typing import Any

from app.application.intent.intent_router import (
    IntentRouter,
    WorkflowRoute,
)
from app.application.intent.intent_workflow_service import (
    IntentWorkflowService,
)
from app.application.software_catalog import (
    SoftwareCatalog,
)
from app.application.software_provisioning_service import (
    SoftwareProvisioningService,
)
from app.application.ticket_service import (
    TicketService,
)
from app.domain.enums import (
    ConfidenceLevel,
    IntentType,
)
from app.domain.intent import (
    AIIntentAnalysis,
)
from app.domain.software import (
    SoftwareProvisioningStatus,
)
from app.infrastructure.itsm.mock_servicenow_client import (
    MockServiceNowClient,
)
from app.infrastructure.provisioning.mock_provisioning_client import (
    MockProvisioningClient,
)


class FakeIntentAnalyzer:
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


def create_workflow():
    analysis = AIIntentAnalysis(
        intent=IntentType.SERVICE_REQUEST,
        category="software",
        subcategory="installation",
        priority=None,
        impact=None,
        urgency=None,
        assignment_group=(
            "desktop_support"
        ),
        summary=(
            "Employee requests Visual Studio Code installation."
        ),
        confidence=ConfidenceLevel.HIGH,
        automation_candidate=False,
        software_name=(
            "Visual Studio Code"
        ),
    )

    analyzer = FakeIntentAnalyzer(
        analysis,
    )

    itsm = MockServiceNowClient()

    ticket_service = TicketService(
        itsm_client=itsm,
    )

    provisioning_client = (
        MockProvisioningClient()
    )

    provisioning_service = (
        SoftwareProvisioningService(
            software_catalog=(
                SoftwareCatalog()
            ),
            ticket_service=ticket_service,
            provisioning_client=(
                provisioning_client
            ),
            itsm_client=itsm,
        )
    )

    workflow = IntentWorkflowService(
        intent_analyzer=analyzer,
        intent_router=IntentRouter(),
        ticket_service=ticket_service,
        software_provisioning_service=(
            provisioning_service
        ),
    )

    return (
        workflow,
        analyzer,
        itsm,
    )


def test_intent_workflow_routes_software_request():
    (
        workflow,
        analyzer,
        itsm,
    ) = create_workflow()

    result = workflow.handle(
        "I need Visual Studio Code "
        "installed on my laptop.",
        user_id="USR-100",
    )

    assert (
        result.analysis.intent
        == IntentType.SERVICE_REQUEST
    )

    assert (
        result.analysis.software_name
        == "Visual Studio Code"
    )

    assert (
        result.decision.route
        == WorkflowRoute.SERVICE_REQUEST
    )

    assert (
        result.response.status
        == SoftwareProvisioningStatus.PROVISIONING
    )

    assert (
        result.response.software_name
        == "Visual Studio Code"
    )

    assert (
        result.response.external_request_number
        is not None
    )

    assert (
        result.response.external_request_number
        .startswith("REQ")
    )

    assert analyzer.requests == [
        "I need Visual Studio Code "
        "installed on my laptop."
    ]

    assert itsm.count() == 1