from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.routers.knowledge import (
    KnowledgeAskRequest,
    KnowledgeAskResponse,
    KnowledgeSearchRequest,
)


def test_knowledge_ask_request_defaults() -> None:
    request = KnowledgeAskRequest(
        query=(
            "How do I troubleshoot "
            "Outlook synchronization?"
        )
    )

    assert request.limit == 5
    assert request.category is None
    assert request.subcategory is None


def test_knowledge_ask_request_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        KnowledgeAskRequest(
            query="Outlook",
            unsupported=True,
        )


def test_knowledge_search_request_supports_hybrid_mode() -> None:
    request = KnowledgeSearchRequest(
        query="Outlook synchronization",
        mode="hybrid",
    )

    assert request.mode == "hybrid"


def test_knowledge_search_request_rejects_invalid_mode() -> None:
    with pytest.raises(ValidationError):
        KnowledgeSearchRequest(
            query="Outlook synchronization",
            mode="invalid",
        )


def test_knowledge_ask_response_contract() -> None:
    response = KnowledgeAskResponse(
        query="Outlook synchronization",
        answer="Restart Outlook.",
        grounded=True,
        confidence="high",
        sources=[],
    )

    assert response.grounded is True
    assert response.confidence == "high"