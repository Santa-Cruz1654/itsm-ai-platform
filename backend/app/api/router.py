from fastapi import APIRouter

from app.api.routers import (
    automations,
    dashboard,
    intent,
    knowledge,
    self_healing,
    software_provisioning,
    tickets,
)

api_router = APIRouter(
    prefix="/api/v1",
)


api_router.include_router(
    automations.router,
)

api_router.include_router(
    tickets.router,
)

api_router.include_router(
    knowledge.router,
)

api_router.include_router(
    intent.router,
)

api_router.include_router(
    self_healing.router,
)

api_router.include_router(
    software_provisioning.router,
)
api_router.include_router(
    dashboard.router,
)