from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.router import api_router
from app.config.settings import get_settings
from app.infrastructure.database.indexes import create_indexes
from app.infrastructure.database.mongodb import MongoDB


settings = get_settings()


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """
    Application lifespan.

    Responsible for initializing and shutting down
    application-scoped infrastructure resources.
    """

    mongodb = MongoDB(
        uri=settings.mongodb_uri,
        database_name=settings.mongodb_database,
    )

    try:
        # Verify that MongoDB is reachable.
        mongodb.ping()

        # Ensure required database indexes exist.
        create_indexes(
            mongodb.database,
        )

        # Store the connection on application state so
        # dependencies can access the same MongoDB client.
        app.state.mongodb = mongodb

        yield

    finally:
        mongodb.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(
    api_router,
)


@app.get("/")
async def root() -> dict[str, str]:
    """
    Application metadata endpoint.
    """

    return {
        "name": settings.app_name,
        "version": "0.1.0",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """
    Basic application health endpoint.
    """

    return {
        "status": "healthy",
        "environment": settings.environment,
    }