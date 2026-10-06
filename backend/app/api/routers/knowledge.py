from __future__ import annotations

from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.api.dependencies import (
    get_knowledge_answer_service,
    get_knowledge_retrieval_service,
)
from app.application.knowledge.answer_service import (
    KnowledgeAnswerService,
)
from app.application.knowledge.retrieval_service import (
    KnowledgeRetrievalService,
)


router = APIRouter(
    prefix="/knowledge",
    tags=["knowledge"],
)


# ======================================================================
# SEARCH
# ======================================================================


class KnowledgeSearchRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    query: str = Field(
        min_length=1,
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    mode: Literal[
        "dense",
        "keyword",
        "hybrid",
    ] = "hybrid"

    category: str | None = None

    subcategory: str | None = None


class KnowledgeSearchItem(BaseModel):
    chunk_id: str

    document_id: str

    content: str

    chunk_index: int

    heading_path: list[str]

    title: str

    category: str

    subcategory: str | None

    version: str

    score: float

    # Retained for API compatibility with the existing response
    # shape. The current retrieval contract exposes one score because
    # Qdrant performs hybrid fusion internally.
    dense_score: float = 0.0

    keyword_score: float = 0.0

    retrieval_method: str


class KnowledgeSearchResponse(BaseModel):
    query: str

    mode: str

    results: list[KnowledgeSearchItem]


# ======================================================================
# ASK / GROUNDED RAG
# ======================================================================


class KnowledgeAskRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    query: str = Field(
        min_length=1,
        max_length=2000,
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=10,
    )

    category: str | None = None

    subcategory: str | None = None


class KnowledgeSourceResponse(BaseModel):
    document_id: str

    chunk_id: str

    chunk_index: int

    title: str

    score: float

    retrieval_method: str


class KnowledgeAskResponse(BaseModel):
    query: str

    answer: str

    grounded: bool

    confidence: Literal[
        "high",
        "medium",
        "low",
    ]

    sources: list[
        KnowledgeSourceResponse
    ]


# ======================================================================
# SEARCH ENDPOINT
# ======================================================================


@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
)
def search_knowledge(
    request: KnowledgeSearchRequest,
    service: KnowledgeRetrievalService = Depends(
        get_knowledge_retrieval_service,
    ),
) -> KnowledgeSearchResponse:
    """
    Search the enterprise knowledge base.

    Supported retrieval modes:

        dense
        keyword
        hybrid
    """

    filters: dict[str, str] = {}

    if request.category:
        filters["category"] = request.category

    if request.subcategory:
        filters["subcategory"] = (
            request.subcategory
        )

    results = service.search(
        request.query,
        mode=request.mode,
        limit=request.limit,
        filters=filters or None,
    )

    items = [
        KnowledgeSearchItem(
            chunk_id=str(
                result.chunk.id
            ),
            document_id=str(
                result.chunk.document_id
            ),
            content=result.chunk.content,
            chunk_index=result.chunk.chunk_index,
            heading_path=list(
                result.chunk.heading_path
            ),
            title=result.chunk.metadata.title,
            category=result.chunk.metadata.category,
            subcategory=(
                result.chunk.metadata.subcategory
            ),
            version=result.chunk.metadata.version,
            score=float(result.score),
            retrieval_method=result.retrieval_method,
        )
        for result in results
    ]

    return KnowledgeSearchResponse(
        query=request.query.strip(),
        mode=request.mode,
        results=items,
    )


# ======================================================================
# GROUNDED ANSWER ENDPOINT
# ======================================================================


@router.post(
    "/ask",
    response_model=KnowledgeAskResponse,
    status_code=status.HTTP_200_OK,
)
def ask_knowledge(
    request: KnowledgeAskRequest,
    service: KnowledgeAnswerService = Depends(
        get_knowledge_answer_service,
    ),
) -> KnowledgeAskResponse:
    """
    Answer an employee question using only retrieved enterprise
    knowledge.

    Flow:

        employee question
              ↓
        hybrid retrieval
              ↓
        grounding gate
              ↓
        bounded RAG context
              ↓
        grounded LLM
              ↓
        answer + sources + confidence
    """

    filters: dict[str, str] = {}

    if request.category:
        filters["category"] = request.category

    if request.subcategory:
        filters["subcategory"] = (
            request.subcategory
        )

    try:
        result = service.ask(
            request.query,
            limit=request.limit,
            filters=filters or None,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return KnowledgeAskResponse(
        query=result.query,
        answer=result.answer,
        grounded=result.grounded,
        confidence=result.confidence,
        sources=[
            KnowledgeSourceResponse(
                document_id=source.document_id,
                chunk_id=source.chunk_id,
                chunk_index=source.chunk_index,
                title=source.title,
                score=source.score,
                retrieval_method=(
                    source.retrieval_method
                ),
            )
            for source in result.sources
        ],
    )