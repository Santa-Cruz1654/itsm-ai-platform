from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TicketType


class SoftwareCatalogItem(BaseModel):
    """
    A software product that is approved for employee provisioning.

    The catalogue is intentionally deterministic.

    AI may identify the requested software, but AI does not decide
    whether arbitrary software may be installed.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    catalog_id: str = Field(
        min_length=1,
    )

    name: str = Field(
        min_length=1,
    )

    version: str = Field(
        min_length=1,
    )

    category: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    aliases: list[str] = Field(
        default_factory=list,
    )

    provisioning_supported: bool = True


class SoftwareProvisioningStatus:
    """
    Controlled provisioning lifecycle values.

    Kept as string constants because the provisioning state belongs
    to the application integration rather than the existing TicketStatus
    lifecycle.
    """

    REQUESTED = "requested"
    PROVISIONING = "provisioning"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class ProvisioningRecord(BaseModel):
    """
    Normalized result returned by the provisioning boundary.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    provisioning_request_id: str = Field(
        min_length=1,
    )

    software_name: str = Field(
        min_length=1,
    )

    user_id: str = Field(
        min_length=1,
    )

    status: str = Field(
        min_length=1,
    )

    message: str = Field(
        min_length=1,
    )

    created_at: datetime

    updated_at: datetime

    ticket_id: str | None = None

    external_request_id: str | None = None

    external_request_number: str | None = None

    ticket_type: TicketType = (
        TicketType.REQUEST
    )