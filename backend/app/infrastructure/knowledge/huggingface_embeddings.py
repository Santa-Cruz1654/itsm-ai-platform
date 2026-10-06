from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.application.ports.embedding_provider import (
    EmbeddingProvider,
)


class HuggingFaceEmbeddingProvider(
    EmbeddingProvider
):

    def __init__(
        self,
        model_name: str = "Alibaba-NLP/gte-modernbert-base",
    ) -> None:
        self._model_name = model_name

        self._model = SentenceTransformer(
            model_name
        )

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        embeddings = self._model.encode_document(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return embeddings.tolist()

    def embed_query(
        self,
        text: str,
    ) -> list[float]:

        embedding = self._model.encode_query(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return embedding.tolist()

    @property
    def dimension(self) -> int:
        return int(
            self._model.get_embedding_dimension()
        )

    @property
    def model_name(self) -> str:
        return self._model_name


@lru_cache(maxsize=4)
def get_embedding_provider(
    model_name: str = "Alibaba-NLP/gte-modernbert-base",
) -> HuggingFaceEmbeddingProvider:

    return HuggingFaceEmbeddingProvider(
        model_name=model_name
    )