from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.software import (
    ProvisioningRecord,
    SoftwareCatalogItem,
)


class SoftwareProvisioningRequest(
    BaseModel
):
    """
    Direct API request for software provisioning.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    user_id: str = Field(
        min_length=1,
    )

    software_name: str = Field(
        min_length=1,
    )

    employee_request: str = Field(
        min_length=1,
    )


class SoftwareProvisioningResponse(
    BaseModel
):
    """
    HTTP representation of provisioning state.
    """

    provisioning_request_id: str

    software_name: str

    user_id: str

    status: str

    message: str

    created_at: datetime

    updated_at: datetime

    ticket_id: str | None = None

    external_request_id: str | None = None

    external_request_number: str | None = None


class SoftwareCatalogResponse(
    BaseModel
):
    catalog_id: str

    name: str

    version: str

    category: str

    description: str

    aliases: list[str]

    provisioning_supported: bool


def to_provisioning_response(
    record: ProvisioningRecord,
) -> SoftwareProvisioningResponse:
    return SoftwareProvisioningResponse(
        provisioning_request_id=(
            record.provisioning_request_id
        ),
        software_name=record.software_name,
        user_id=record.user_id,
        status=record.status,
        message=record.message,
        created_at=record.created_at,
        updated_at=record.updated_at,
        ticket_id=record.ticket_id,
        external_request_id=(
            record.external_request_id
        ),
        external_request_number=(
            record.external_request_number
        ),
    )


def to_catalog_response(
    item: SoftwareCatalogItem,
) -> SoftwareCatalogResponse:
    return SoftwareCatalogResponse(
        catalog_id=item.catalog_id,
        name=item.name,
        version=item.version,
        category=item.category,
        description=item.description,
        aliases=item.aliases,
        provisioning_supported=(
            item.provisioning_supported
        ),
    )