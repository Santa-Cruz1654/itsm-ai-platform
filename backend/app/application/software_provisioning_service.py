from __future__ import annotations

from datetime import datetime, timezone

from app.application.ports.itsm_client import (
    ITSMClient,
)
from app.application.ports.provisioning_client import (
    ProvisioningClient,
)
from app.application.software_catalog import (
    SoftwareCatalog,
)
from app.application.ticket_service import (
    TicketService,
)
from app.domain.enums import (
    TicketStatus,
    TicketType,
)
from app.domain.software import (
    ProvisioningRecord,
    SoftwareProvisioningStatus,
)

class SoftwareProvisioningService:
    """
    Application workflow for controlled software provisioning.

    Workflow:

        Employee request
            ↓
        Software catalogue
            ↓
        Internal service request
            ↓
        External ITSM request
            ↓
        Mock provisioning API
            ↓
        Provisioning status
            ↓
        ITSM status update

    The service never installs software itself.
    """

    def __init__(
        self,
        *,
        software_catalog: SoftwareCatalog,
        ticket_service: TicketService,
        provisioning_client: ProvisioningClient,
        itsm_client: ITSMClient,
    ) -> None:
        self._software_catalog = (
            software_catalog
        )

        self._ticket_service = (
            ticket_service
        )

        self._provisioning_client = (
            provisioning_client
        )

        self._itsm_client = itsm_client

        # In-memory correlation for the mock workflow.
        #
        # A production implementation would persist this state
        # in MongoDB.
        self._ticket_by_provisioning_id: dict[
            str,
            str,
        ] = {}

        self._external_ticket_by_provisioning_id: dict[
            str,
            str,
        ] = {}

    # ------------------------------------------------------------------
    # Create provisioning request
    # ------------------------------------------------------------------

    def request_installation(
        self,
        *,
        user_id: str,
        software_name: str,
        employee_request: str,
    ) -> ProvisioningRecord:
        """
        Submit a controlled software provisioning request.
        """

        user_id = user_id.strip()
        software_name = software_name.strip()
        employee_request = (
            employee_request.strip()
        )

        if not user_id:
            raise ValueError(
                "User ID cannot be empty."
            )

        if not software_name:
            raise ValueError(
                "Software name cannot be empty."
            )

        if not employee_request:
            raise ValueError(
                "Employee request cannot be empty."
            )

        # --------------------------------------------------------------
        # Catalogue resolution
        # --------------------------------------------------------------

        software = (
            self._software_catalog.get(
                software_name,
            )
        )

        if software is None:
            now = (
                __import__(
                    "datetime"
                )
                .datetime.now(
                    __import__(
                        "datetime"
                    ).timezone.utc
                )
            )

            return ProvisioningRecord(
                provisioning_request_id=(
                    "REJECTED"
                ),
                software_name=software_name,
                user_id=user_id,
                status=(
                    SoftwareProvisioningStatus.REJECTED
                ),
                message=(
                    f"'{software_name}' is not available "
                    "in the approved software catalogue."
                ),
                created_at=now,
                updated_at=now,
            )

        if not software.provisioning_supported:
            now = (
                __import__(
                    "datetime"
                )
                .datetime.now(
                    __import__(
                        "datetime"
                    ).timezone.utc
                )
            )

            return ProvisioningRecord(
                provisioning_request_id=(
                    "REJECTED"
                ),
                software_name=software.name,
                user_id=user_id,
                status=(
                    SoftwareProvisioningStatus.REJECTED
                ),
                message=(
                    f"{software.name} is present in the "
                    "catalogue but is not currently "
                    "provisionable."
                ),
                created_at=now,
                updated_at=now,
            )

        # --------------------------------------------------------------
        # Create IT service request
        # --------------------------------------------------------------

        ticket = (
            self._ticket_service.create_ticket(
                ticket_type=TicketType.REQUEST,
                title=(
                    f"Software installation: "
                    f"{software.name}"
                ),
                description=employee_request,
                user_id=user_id,
            )
        )

        # --------------------------------------------------------------
        # Verify external ITSM synchronization
        # --------------------------------------------------------------

        if (
            ticket.external_sync_status
            != "synchronized"
        ):
            now = (
                __import__(
                    "datetime"
                )
                .datetime.now(
                    __import__(
                        "datetime"
                    ).timezone.utc
                )
            )

            return ProvisioningRecord(
                provisioning_request_id=(
                    "FAILED"
                ),
                software_name=software.name,
                user_id=user_id,
                status=(
                    SoftwareProvisioningStatus.FAILED
                ),
                message=(
                    "The ServiceNow request could not "
                    "be synchronized."
                ),
                created_at=now,
                updated_at=now,
                ticket_id=ticket.ticket_id,
            )

        # --------------------------------------------------------------
        # Submit provisioning request
        # --------------------------------------------------------------

        record = (
            self._provisioning_client.submit(
                user_id=user_id,
                software=software,
                ticket_id=ticket.ticket_id,
                external_request_id=(
                    ticket.external_ticket_id
                ),
                external_request_number=(
                    ticket.external_ticket_number
                ),
            )
        )

        self._ticket_by_provisioning_id[
            record.provisioning_request_id
        ] = ticket.ticket_id

        if ticket.external_ticket_id:
            self._external_ticket_by_provisioning_id[
                record.provisioning_request_id
            ] = ticket.external_ticket_id

            # Keep ServiceNow synchronized with the
            # provisioning lifecycle.
            self._itsm_client.update_ticket(
                ticket.external_ticket_id,
                status=TicketStatus.OPEN,
            )

        return record

    # ------------------------------------------------------------------
    # Get provisioning status
    # ------------------------------------------------------------------

    def get_status(
        self,
        provisioning_request_id: str,
    ) -> ProvisioningRecord:
        record = (
            self._provisioning_client.get_status(
                provisioning_request_id,
            )
        )

        external_ticket_id = (
            self._external_ticket_by_provisioning_id.get(
                provisioning_request_id,
            )
        )

        if (
            external_ticket_id
            and record.status
            == SoftwareProvisioningStatus.COMPLETED
        ):
            self._itsm_client.update_ticket(
                external_ticket_id,
                status=TicketStatus.RESOLVED,
            )

        return record

    # ------------------------------------------------------------------
    # Catalogue
    # ------------------------------------------------------------------

    def list_catalogue(self):
        return self._software_catalog.list_items()