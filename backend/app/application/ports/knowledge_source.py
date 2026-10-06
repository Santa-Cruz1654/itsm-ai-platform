from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.domain.knowledge import KnowledgeDocument


class KnowledgeSource(ABC):

    @abstractmethod
    def load(
        self,
        path: Path,
    ) -> KnowledgeDocument:
        raise NotImplementedError

    @abstractmethod
    def list_documents(
        self,
        root: Path,
    ) -> list[Path]:
        raise NotImplementedError