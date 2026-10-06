from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from app.api.dependencies import (
    get_software_provisioning_service,
)
from app.api.schemas.software_provisioning import (
    SoftwareCatalogResponse,
    SoftwareProvisioningRequest,
    SoftwareProvisioningResponse,
    to_catalog_response,
    to_provisioning_response,
)
from app.application.software_provisioning_service import (
    SoftwareProvisioningService,
)


router = APIRouter(
    prefix="/software-provisioning",
    tags=["Software Provisioning"],
)


@router.get(
    "/catalog",
    response_model=list[
        SoftwareCatalogResponse
    ],
)
def list_software_catalog(
    service: SoftwareProvisioningService = Depends(
        get_software_provisioning_service,
    ),
) -> list[SoftwareCatalogResponse]:
    """
    Return the approved software catalogue.
    """

    return [
        to_catalog_response(item)
        for item in service.list_catalogue()
    ]


@router.post(
    "",
    response_model=SoftwareProvisioningResponse,
    status_code=status.HTTP_201_CREATED,
)
def request_software_provisioning(
    request: SoftwareProvisioningRequest,
    service: SoftwareProvisioningService = Depends(
        get_software_provisioning_service,
    ),
) -> SoftwareProvisioningResponse:
    """
    Create a software provisioning request.
    """

    record = service.request_installation(
        user_id=request.user_id,
        software_name=request.software_name,
        employee_request=(
            request.employee_request
        ),
    )

    return to_provisioning_response(
        record,
    )


@router.get(
    "/{provisioning_request_id}",
    response_model=SoftwareProvisioningResponse,
)
def get_software_provisioning_status(
    provisioning_request_id: str,
    service: SoftwareProvisioningService = Depends(
        get_software_provisioning_service,
    ),
) -> SoftwareProvisioningResponse:
    """
    Retrieve and update the current provisioning state.
    """

    record = service.get_status(
        provisioning_request_id,
    )

    return to_provisioning_response(
        record,
    )