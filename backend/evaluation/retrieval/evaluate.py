from __future__ import annotations

import json
from pathlib import Path

from app.application.knowledge.retrieval_service import (
    KnowledgeRetrievalService,
)
from app.infrastructure.knowledge.huggingface_embeddings import (
    get_embedding_provider,
)
from app.infrastructure.knowledge.qdrant_vector_store import (
    QdrantVectorStore,
)


DATASET_PATH = Path(
    "evaluation/retrieval/dataset.json"
)


def recall_at_k(
    retrieved: list[str],
    relevant: set[str],
    k: int,
) -> float:

    if not relevant:
        return 0.0

    top_k = set(
        retrieved[:k]
    )

    return float(
        bool(
            top_k & relevant
        )
    )


def reciprocal_rank(
    retrieved: list[str],
    relevant: set[str],
) -> float:

    for rank, document_id in enumerate(
        retrieved,
        start=1,
    ):

        if document_id in relevant:
            return 1.0 / rank

    return 0.0


def evaluate_mode(
    service: KnowledgeRetrievalService,
    dataset: list[dict],
    mode: str,
) -> tuple[float, float]:

    recalls: list[float] = []
    reciprocal_ranks: list[float] = []

    for item in dataset:

        query = item["query"]

        relevant = set(
            item["relevant_document_ids"]
        )

        if mode == "dense":

            results = service.dense_search(
                query,
                limit=5,
            )

            retrieved = [
                result.chunk.metadata.document_id
                for result in results
            ]

        elif mode == "keyword":

            results = service.keyword_search(
                query,
                limit=5,
            )

            retrieved = [
                result.chunk.metadata.document_id
                for result in results
            ]

        else:

            results = service.hybrid_search(
                query,
                limit=5,
            )

            retrieved = [
                result.chunk.metadata.document_id
                for result in results
            ]

        recalls.append(
            recall_at_k(
                retrieved,
                relevant,
                5,
            )
        )

        reciprocal_ranks.append(
            reciprocal_rank(
                retrieved,
                relevant,
            )
        )

    recall = (
        sum(recalls)
        / len(recalls)
        if recalls
        else 0.0
    )

    mrr = (
        sum(reciprocal_ranks)
        / len(reciprocal_ranks)
        if reciprocal_ranks
        else 0.0
    )

    return recall, mrr


def main() -> None:

    dataset = json.loads(
        DATASET_PATH.read_text(
            encoding="utf-8"
        )
    )

    embeddings = (
        get_embedding_provider()
    )

    vector_store = QdrantVectorStore(
        embedding_dimension=embeddings.dimension
    )

    service = KnowledgeRetrievalService(
        embedding_provider=embeddings,
        vector_store=vector_store,
    )

    print(
        "\nRAG Retrieval Evaluation\n"
    )

    for mode in (
        "dense",
        "keyword",
        "hybrid",
    ):

        recall, mrr = evaluate_mode(
            service,
            dataset,
            mode,
        )

        print(
            f"{mode.upper():<10} "
            f"Recall@5={recall:.3f} "
            f"MRR={mrr:.3f}"
        )


if __name__ == "__main__":
    main()