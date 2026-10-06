from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from app.application.ports.provisioning_client import (
    ProvisioningClient,
)
from app.domain.software import (
    ProvisioningRecord,
    SoftwareCatalogItem,
    SoftwareProvisioningStatus,
)


class MockProvisioningClient(
    ProvisioningClient
):
    """
    Safe in-memory provisioning adapter.

    It does NOT install software.

    It simulates an enterprise endpoint such as:

        Intune
        SCCM
        Jamf
        internal software deployment API

    Lifecycle:

        submit()
            ↓
        PROVISIONING
            ↓
        first get_status()
            ↓
        COMPLETED
    """

    def __init__(self) -> None:
        self._records: dict[
            str,
            ProvisioningRecord,
        ] = {}

        self._poll_counts: dict[
            str,
            int,
        ] = {}

        self._lock = Lock()

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------

    def submit(
        self,
        *,
        user_id: str,
        software: SoftwareCatalogItem,
        ticket_id: str,
        external_request_id: str | None,
        external_request_number: str | None,
    ) -> ProvisioningRecord:
        if not user_id.strip():
            raise ValueError(
                "User ID cannot be empty."
            )

        if not ticket_id.strip():
            raise ValueError(
                "Ticket ID cannot be empty."
            )

        now = datetime.now(
            timezone.utc,
        )

        provisioning_id = (
            f"PROV-{uuid4()}"
        )

        record = ProvisioningRecord(
            provisioning_request_id=(
                provisioning_id
            ),
            software_name=software.name,
            user_id=user_id.strip(),
            status=(
                SoftwareProvisioningStatus.PROVISIONING
            ),
            message=(
                f"{software.name} provisioning "
                "has been submitted."
            ),
            created_at=now,
            updated_at=now,
            ticket_id=ticket_id,
            external_request_id=(
                external_request_id
            ),
            external_request_number=(
                external_request_number
            ),
        )

        with self._lock:
            self._records[
                provisioning_id
            ] = record

            self._poll_counts[
                provisioning_id
            ] = 0

        return deepcopy(record)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(
        self,
        provisioning_request_id: str,
    ) -> ProvisioningRecord:
        provisioning_request_id = (
            provisioning_request_id.strip()
        )

        if not provisioning_request_id:
            raise ValueError(
                "Provisioning request ID cannot be empty."
            )

        with self._lock:
            record = self._records.get(
                provisioning_request_id,
            )

            if record is None:
                raise KeyError(
                    "Provisioning request not found: "
                    f"{provisioning_request_id}"
                )

            poll_count = (
                self._poll_counts.get(
                    provisioning_request_id,
                    0,
                )
            )

            # First status check completes the mock operation.
            if (
                record.status
                == SoftwareProvisioningStatus.PROVISIONING
            ):
                poll_count += 1

                self._poll_counts[
                    provisioning_request_id
                ] = poll_count

                if poll_count >= 1:
                    now = datetime.now(
                        timezone.utc,
                    )

                    record = record.model_copy(
                        update={
                            "status": (
                                SoftwareProvisioningStatus.COMPLETED
                            ),
                            "message": (
                                f"{record.software_name} "
                                "was provisioned successfully."
                            ),
                            "updated_at": now,
                        }
                    )

                    self._records[
                        provisioning_request_id
                    ] = record

            return deepcopy(record)

    # ------------------------------------------------------------------
    # Test helper
    # ------------------------------------------------------------------

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
            self._poll_counts.clear()