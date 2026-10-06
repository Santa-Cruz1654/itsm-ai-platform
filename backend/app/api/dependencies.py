from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from app.application.automation_service import (
    AutomationService,
)
from app.application.intent.intent_analyzer import (
    IntentAnalyzer,
)
from app.application.intent.intent_router import (
    IntentRouter,
)
from app.application.intent.intent_workflow_service import (
    IntentWorkflowService,
)
from app.application.knowledge.answer_service import (
    KnowledgeAnswerService,
)
from app.application.knowledge.context_assembly_service import (
    RAGContextAssemblyService,
)
from app.application.knowledge.rag_generation import (
    RAGGenerationService,
)
from app.application.knowledge.retrieval_service import (
    KnowledgeRetrievalService,
)
from app.application.ports.audit_repository import (
    AuditRepository,
)
from app.application.ports.llm_provider import (
    LLMProvider,
)
from app.application.self_healing_service import (
    SelfHealingWorkflowService,
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
from app.application.dashboard_service import (
    DashboardService,
)

from app.config.settings import get_settings

from app.infrastructure.automation.mock_password_reset import (
    MockPasswordResetTool,
)
from app.infrastructure.database.mongodb import (
    MongoDB,
)
from app.infrastructure.knowledge.huggingface_embeddings import (
    get_embedding_provider,
)
from app.infrastructure.knowledge.qdrant_vector_store import (
    QdrantVectorStore,
)
from app.infrastructure.llm.huggingface_provider import (
    HuggingFaceLLMProvider,
)
from app.infrastructure.provisioning.mock_provisioning_client import (
    MockProvisioningClient,
)
from app.infrastructure.repositories.mongo_audit_repository import (
    MongoAuditRepository,
)
from app.infrastructure.repositories.mongo_ticket_repository import (
    MongoTicketRepository,
)
from app.infrastructure.itsm.mock_servicenow_client import (
    MockServiceNowClient,
)


# ======================================================================
# DATABASE
# ======================================================================


def get_mongodb(
    request: Request,
) -> MongoDB:
    """
    Return the application-scoped MongoDB connection.

    MongoDB is initialized during FastAPI startup and stored on
    app.state.
    """

    mongodb: MongoDB | None = getattr(
        request.app.state,
        "mongodb",
        None,
    )

    if mongodb is None:
        raise RuntimeError(
            "MongoDB has not been initialized."
        )

    return mongodb


# ======================================================================
# ITSM INTEGRATION
# ======================================================================


@lru_cache(maxsize=1)
def get_itsm_client() -> MockServiceNowClient:
    """
    Return the canonical application-scoped ITSM client.

    The current implementation uses the controlled
    MockServiceNowClient for the hackathon/demo environment.

    All application workflows that interact with the ITSM
    integration should resolve the client through this dependency.

    This keeps the application layer independent from the concrete
    ServiceNow implementation and ensures that TicketService,
    SelfHealingWorkflowService, SoftwareProvisioningService, and
    IntentWorkflowService use the same application-scoped adapter.
    """

    return MockServiceNowClient()


# ======================================================================
# EXISTING APPLICATION SERVICES
# ======================================================================


def get_automation_service() -> AutomationService:
    """
    Dependency provider for the automation application service.
    """

    return AutomationService()


def get_ticket_service(
    mongodb: Annotated[
        MongoDB,
        Depends(get_mongodb),
    ],
) -> TicketService:
    """
    Dependency provider for the Ticket application service.

    Production API requests use the MongoDB-backed repository.

    The TicketService receives the canonical application-scoped
    ITSM adapter.
    """

    repository = MongoTicketRepository(
        mongodb.database,
    )

    return TicketService(
        ticket_repository=repository,
        itsm_client=get_itsm_client(),
    )

def get_dashboard_service(
    mongodb: Annotated[
        MongoDB,
        Depends(get_mongodb),
    ],
) -> DashboardService:
    """
    Dependency provider for the reviewer-facing
    ITSM dashboard.

    The dashboard reads tickets through the same
    MongoDB-backed repository used by the production
    ticket workflow.
    """

    repository = MongoTicketRepository(
        mongodb.database,
    )

    return DashboardService(
        ticket_repository=repository,
    )
# ----------------------------------------------------------------------
# Backward-compatible ITSM dependency names
# ----------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_intent_itsm_client() -> MockServiceNowClient:
    """
    Backward-compatible ITSM dependency name used by existing
    intent/ticket composition.

    Delegates to the canonical get_itsm_client() provider.
    """

    return get_itsm_client()


# ======================================================================
# SOFTWARE PROVISIONING
# ======================================================================


@lru_cache(maxsize=1)
def get_software_catalog() -> SoftwareCatalog:
    """
    Application-scoped approved software catalogue.
    """

    return SoftwareCatalog()


@lru_cache(maxsize=1)
def get_provisioning_client() -> MockProvisioningClient:
    """
    Controlled mock provisioning adapter.

    This is the current hackathon/demo implementation.
    """

    return MockProvisioningClient()


@lru_cache(maxsize=1)
def get_software_itsm_client() -> MockServiceNowClient:
    """
    Backward-compatible ITSM dependency for the software
    provisioning workflow.

    The canonical application-scoped ITSM client is returned so
    software provisioning shares the same adapter as the other
    application workflows.
    """

    return get_itsm_client()


def get_software_provisioning_service(
    ticket_service: Annotated[
        TicketService,
        Depends(get_ticket_service),
    ],
) -> SoftwareProvisioningService:
    """
    Compose the software provisioning application service.

    Dependency graph:

        SoftwareCatalog
              |
        TicketService
              |
        MockProvisioningClient
              |
        MockServiceNowClient
              |
        SoftwareProvisioningService
    """

    return SoftwareProvisioningService(
        software_catalog=get_software_catalog(),
        ticket_service=ticket_service,
        provisioning_client=get_provisioning_client(),
        itsm_client=get_itsm_client(),
    )


# ======================================================================
# KNOWLEDGE INFRASTRUCTURE
# ======================================================================


@lru_cache(maxsize=1)
def get_knowledge_vector_store() -> QdrantVectorStore:
    """
    Application-scoped Qdrant vector store.
    """

    embedding_provider = (
        get_embedding_provider()
    )

    return QdrantVectorStore(
        embedding_dimension=(
            embedding_provider.dimension
        ),
    )


@lru_cache(maxsize=1)
def get_knowledge_retrieval_service() -> (
    KnowledgeRetrievalService
):
    """
    Application-scoped knowledge retrieval service.
    """

    embedding_provider = (
        get_embedding_provider()
    )

    vector_store = (
        get_knowledge_vector_store()
    )

    return KnowledgeRetrievalService(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )


# ======================================================================
# LLM INFRASTRUCTURE
# ======================================================================


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """
    Return the concrete LLM provider.

    The application layer depends only on LLMProvider.
    """

    get_settings()

    return HuggingFaceLLMProvider()


# ======================================================================
# RAG
# ======================================================================


@lru_cache(maxsize=1)
def get_rag_context_assembly_service() -> (
    RAGContextAssemblyService
):
    """
    Application-scoped RAG context assembler.
    """

    return RAGContextAssemblyService(
        max_chunks=5,
        max_context_characters=12000,
    )


@lru_cache(maxsize=1)
def get_rag_generation_service() -> (
    RAGGenerationService
):
    """
    Application-scoped grounded generation service.
    """

    return RAGGenerationService(
        llm_provider=get_llm_provider(),
    )


@lru_cache(maxsize=1)
def get_knowledge_answer_service() -> (
    KnowledgeAnswerService
):
    """
    Compose the complete employee-facing knowledge workflow.

    Dependency graph:

        KnowledgeRetrievalService
                  |
                  v
        RAGContextAssemblyService
                  |
                  v
        RAGGenerationService
                  |
                  v
        KnowledgeAnswerService
    """

    return KnowledgeAnswerService(
        retrieval_service=(
            get_knowledge_retrieval_service()
        ),
        context_assembly_service=(
            get_rag_context_assembly_service()
        ),
        generation_service=(
            get_rag_generation_service()
        ),
    )


# ======================================================================
# AUDIT
# ======================================================================


def get_audit_repository(
    mongodb: Annotated[
        MongoDB,
        Depends(get_mongodb),
    ],
) -> AuditRepository:
    """
    Production MongoDB-backed audit repository.
    """

    return MongoAuditRepository(
        mongodb.database,
    )


# ======================================================================
# AUTOMATION TOOLS
# ======================================================================


@lru_cache(maxsize=1)
def get_password_reset_tool() -> (
    MockPasswordResetTool
):
    """
    Return the controlled password-reset automation tool.

    This remains a mock tool.

    Do not replace this with arbitrary dynamic tool execution.
    """

    return MockPasswordResetTool()


# ======================================================================
# SELF-HEALING
# ======================================================================


def get_self_healing_service(
    automation_service: Annotated[
        AutomationService,
        Depends(get_automation_service),
    ],
    ticket_service: Annotated[
        TicketService,
        Depends(get_ticket_service),
    ],
    knowledge_retrieval_service: Annotated[
        KnowledgeRetrievalService,
        Depends(
            get_knowledge_retrieval_service,
        ),
    ],
    audit_repository: Annotated[
        AuditRepository,
        Depends(get_audit_repository),
    ],
    password_reset_tool: Annotated[
        MockPasswordResetTool,
        Depends(get_password_reset_tool),
    ],
    itsm_client: Annotated[
        MockServiceNowClient,
        Depends(get_itsm_client),
    ],
) -> SelfHealingWorkflowService:
    """
    Construct the self-healing workflow from explicit
    application dependencies.

    The workflow requires:

    - automation service
    - ticket service
    - approved knowledge retrieval
    - audit repository
    - controlled password-reset tool
    - shared application-scoped ITSM client
    """

    return SelfHealingWorkflowService(
        automation_service=automation_service,
        ticket_service=ticket_service,
        knowledge_retrieval_service=(
            knowledge_retrieval_service
        ),
        audit_repository=audit_repository,
        itsm_client=itsm_client,
        password_reset_tool=password_reset_tool,
    )


# ======================================================================
# INTENT
# ======================================================================


@lru_cache(maxsize=1)
def get_intent_analyzer() -> IntentAnalyzer:
    """
    Application-scoped intent analyzer.
    """

    return IntentAnalyzer(
        llm_provider=get_llm_provider(),
    )


@lru_cache(maxsize=1)
def get_intent_router() -> IntentRouter:
    """
    Application-scoped deterministic intent router.
    """

    return IntentRouter()


# ======================================================================
# COMPLETE INTENT WORKFLOW
# ======================================================================


def get_intent_workflow_service(
    intent_analyzer: Annotated[
        IntentAnalyzer,
        Depends(get_intent_analyzer),
    ],
    intent_router: Annotated[
        IntentRouter,
        Depends(get_intent_router),
    ],
    knowledge_retrieval_service: Annotated[
        KnowledgeRetrievalService,
        Depends(
            get_knowledge_retrieval_service,
        ),
    ],
    mongodb: Annotated[
        MongoDB,
        Depends(get_mongodb),
    ],
    self_healing_service: Annotated[
        SelfHealingWorkflowService,
        Depends(get_self_healing_service),
    ],
    software_provisioning_service: Annotated[
        SoftwareProvisioningService,
        Depends(
            get_software_provisioning_service,
        ),
    ],
) -> IntentWorkflowService:
    """
    Compose the complete AI-assisted ITSM workflow.

    Dependency graph:

        LLMProvider
             |
             v
        IntentAnalyzer
             |
             v
        IntentRouter
             |
             v
        IntentWorkflowService
             |
             +-- KnowledgeRetrievalService
             |
             +-- TicketService
             |       |
             |       v
             |   MockServiceNowClient
             |
             +-- SelfHealingWorkflowService
             |       |
             |       v
             |   MockServiceNowClient
             |
             +-- SoftwareProvisioningService
                     |
                     v
                 MockServiceNowClient

    All ITSM-dependent workflows use the same application-scoped
    canonical ITSM adapter.
    """

    ticket_repository = MongoTicketRepository(
        mongodb.database,
    )

    ticket_service = TicketService(
        ticket_repository=ticket_repository,
        itsm_client=get_itsm_client(),
    )

    return IntentWorkflowService(
        intent_analyzer=intent_analyzer,
        intent_router=intent_router,
        knowledge_retrieval_service=(
            knowledge_retrieval_service
        ),
        ticket_service=ticket_service,
        self_healing_service=(
            self_healing_service
        ),
        software_provisioning_service=(
            software_provisioning_service
        ),
    )
