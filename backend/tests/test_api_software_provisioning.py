from __future__ import annotations

import pytest
from fastapi.testclient import (
    TestClient,
)

from app.api.dependencies import (
    get_intent_workflow_service,
    get_software_provisioning_service,
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
from app.infrastructure.itsm.mock_servicenow_client import (
    MockServiceNowClient,
)
from app.infrastructure.provisioning.mock_provisioning_client import (
    MockProvisioningClient,
)
from app.application.intent.intent_router import (
    IntentRouter,
)
from app.main import app


class FakeIntentAnalyzer:
    def analyze(
        self,
        employee_request: str,
    ) -> AIIntentAnalysis:
        return AIIntentAnalysis(
            intent=IntentType.SERVICE_REQUEST,
            category="software",
            subcategory="installation",
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


def create_service():
    itsm = MockServiceNowClient()

    ticket_service = TicketService(
        itsm_client=itsm,
    )

    provisioning = (
        MockProvisioningClient()
    )

    service = (
        SoftwareProvisioningService(
            software_catalog=(
                SoftwareCatalog()
            ),
            ticket_service=ticket_service,
            provisioning_client=provisioning,
            itsm_client=itsm,
        )
    )

    return (
        service,
        itsm,
    )


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()

    yield

    app.dependency_overrides.clear()


def test_software_catalog_endpoint():
    service, _ = create_service()

    app.dependency_overrides[
        get_software_provisioning_service
    ] = lambda: service

    client = TestClient(app)

    response = client.get(
        "/api/v1/software-provisioning/catalog"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    names = {
        item["name"]
        for item in data
    }

    assert (
        "Visual Studio Code"
        in names
    )


def test_software_provisioning_api():
    service, itsm = create_service()

    app.dependency_overrides[
        get_software_provisioning_service
    ] = lambda: service

    client = TestClient(app)

    response = client.post(
        "/api/v1/software-provisioning",
        json={
            "user_id": "USR-API-001",
            "software_name": (
                "Visual Studio Code"
            ),
            "employee_request": (
                "I need Visual Studio Code "
                "installed on my laptop."
            ),
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert (
        data["software_name"]
        == "Visual Studio Code"
    )

    assert (
        data["status"]
        == "provisioning"
    )

    assert (
        data["external_request_number"]
        .startswith("REQ")
    )

    assert (
        data["provisioning_request_id"]
        .startswith("PROV-")
    )

    assert itsm.count() == 1


def test_software_provisioning_status_endpoint():
    service, _ = create_service()

    app.dependency_overrides[
        get_software_provisioning_service
    ] = lambda: service

    client = TestClient(app)

    create_response = client.post(
        "/api/v1/software-provisioning",
        json={
            "user_id": "USR-API-002",
            "software_name": (
                "Visual Studio Code"
            ),
            "employee_request": (
                "Please install VS Code."
            ),
        },
    )

    assert (
        create_response.status_code
        == 201
    )

    provisioning_id = (
        create_response.json()[
            "provisioning_request_id"
        ]
    )

    status_response = client.get(
        "/api/v1/software-provisioning/"
        f"{provisioning_id}",
    )

    assert (
        status_response.status_code
        == 200
    )

    data = status_response.json()

    assert (
        data["status"]
        == "completed"
    )


def test_intent_api_can_reach_software_provisioning():
    (
        service,
        _itsm,
    ) = create_service()

    workflow = IntentWorkflowService(
        intent_analyzer=(
            FakeIntentAnalyzer()
        ),
        intent_router=IntentRouter(),
        ticket_service=TicketService(
            itsm_client=_itsm,
        ),
        software_provisioning_service=(
            service
        ),
    )

    app.dependency_overrides[
        get_intent_workflow_service
    ] = lambda: workflow

    client = TestClient(app)

    response = client.post(
        "/api/v1/intent",
        json={
            "user_id": "USR-API-003",
            "employee_request": (
                "I need Visual Studio Code "
                "installed on my laptop."
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["analysis"]["intent"]
        == "service_request"
    )

    assert (
        data["analysis"]["software_name"]
        == "Visual Studio Code"
    )

    assert (
        data["decision"]["route"]
        == "service_request"
    )

    assert (
        data["response"]["status"]
        == "provisioning"
    )

    assert (
        data["response"]["external_request_number"]
        .startswith("REQ")
    )