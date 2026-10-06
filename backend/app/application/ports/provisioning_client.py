from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.software import (
    ProvisioningRecord,
    SoftwareCatalogItem,
)


class ProvisioningClient(ABC):
    """
    Application port for software provisioning.

    The application layer does not know whether provisioning is
    performed by:

        - Microsoft Intune
        - SCCM
        - Jamf
        - an internal endpoint
        - a mock API

    It only depends on this contract.
    """

    @abstractmethod
    def submit(
        self,
        *,
        user_id: str,
        software: SoftwareCatalogItem,
        ticket_id: str,
        external_request_id: str | None,
        external_request_number: str | None,
    ) -> ProvisioningRecord:
        """
        Submit a provisioning request.
        """
        raise NotImplementedError

    @abstractmethod
    def get_status(
        self,
        provisioning_request_id: str,
    ) -> ProvisioningRecord:
        """
        Retrieve the current provisioning status.
        """
        raise NotImplementedError