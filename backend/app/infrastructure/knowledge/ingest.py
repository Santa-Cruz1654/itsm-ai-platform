from pathlib import Path

from app.application.knowledge.ingestion_service import (
    KnowledgeIngestionService,
)
from app.infrastructure.knowledge.huggingface_embeddings import (
    get_embedding_provider,
)
from app.infrastructure.knowledge.markdown_source import (
    MarkdownKnowledgeSource,
)
from app.infrastructure.knowledge.qdrant_vector_store import (
    QdrantVectorStore,
)
from app.infrastructure.knowledge.semantic_chunker import (
    SemanticChunker,
)


def main() -> None:
    root = Path("knowledge")

    embeddings = (
        get_embedding_provider()
    )

    source = (
        MarkdownKnowledgeSource()
    )

    chunker = SemanticChunker(
        embeddings,
        similarity_threshold=0.55,
        max_characters=5000,
    )

    vector_store = QdrantVectorStore(
        embedding_dimension=(
            embeddings.dimension
        )
    )

    service = KnowledgeIngestionService(
        source=source,
        embedding_provider=embeddings,
        vector_store=vector_store,
    )

    results = service.ingest_directory(
        root,
        chunker,
    )

    print(
        "\nKnowledge ingestion complete.\n"
    )

    for path, count in results.items():
        print(
            f"{path}: {count} chunks"
        )


if __name__ == "__main__":
    main()