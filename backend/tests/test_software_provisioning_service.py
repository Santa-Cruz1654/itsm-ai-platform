from __future__ import annotations

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
    TicketStatus,
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


def create_service():
    itsm_client = (
        MockServiceNowClient()
    )

    ticket_service = TicketService(
        itsm_client=itsm_client,
    )

    provisioning_client = (
        MockProvisioningClient()
    )

    service = (
        SoftwareProvisioningService(
            software_catalog=(
                SoftwareCatalog()
            ),
            ticket_service=ticket_service,
            provisioning_client=(
                provisioning_client
            ),
            itsm_client=itsm_client,
        )
    )

    return (
        service,
        itsm_client,
        provisioning_client,
    )


def test_visual_studio_code_request_creates_service_request():
    (
        service,
        itsm,
        _provisioning,
    ) = create_service()

    result = (
        service.request_installation(
            user_id="USR-001",
            software_name=(
                "Visual Studio Code"
            ),
            employee_request=(
                "I need Visual Studio Code "
                "installed on my laptop."
            ),
        )
    )

    assert result.status == (
        SoftwareProvisioningStatus.PROVISIONING
    )

    assert result.software_name == (
        "Visual Studio Code"
    )

    assert result.ticket_id is not None

    assert (
        result.external_request_number
        is not None
    )

    assert (
        result.external_request_number
        .startswith("REQ")
    )

    assert itsm.count() == 1


def test_provisioning_status_changes_to_completed():
    (
        service,
        itsm,
        _provisioning,
    ) = create_service()

    created = (
        service.request_installation(
            user_id="USR-002",
            software_name=(
                "Visual Studio Code"
            ),
            employee_request=(
                "Please install VS Code."
            ),
        )
    )

    assert created.status == (
        SoftwareProvisioningStatus.PROVISIONING
    )

    completed = service.get_status(
        created.provisioning_request_id,
    )

    assert completed.status == (
        SoftwareProvisioningStatus.COMPLETED
    )

    assert (
        completed.message
        == "Visual Studio Code was provisioned successfully."
    )

    assert itsm.count() == 1

    assert (
        completed.external_request_id
        is not None
    )

    external_record = itsm.get_ticket(
        completed.external_request_id,
    )

    assert external_record is not None

    assert external_record.status == (
        TicketStatus.RESOLVED.value
    )


def test_unsupported_software_is_rejected():
    (
        service,
        itsm,
        _provisioning,
    ) = create_service()

    result = (
        service.request_installation(
            user_id="USR-003",
            software_name=(
                "Unsupported Enterprise Software"
            ),
            employee_request=(
                "Install unsupported software."
            ),
        )
    )

    assert result.status == (
        SoftwareProvisioningStatus.REJECTED
    )

    assert (
        result.ticket_id is None
    )

    assert (
        result.external_request_number
        is None
    )

    assert itsm.count() == 0