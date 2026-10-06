from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.domain.knowledge import (
    KnowledgeDocument,
    KnowledgeMetadata,
    deterministic_document_id,
)


class MarkdownKnowledgeSource:
    """
    Infrastructure adapter for Markdown knowledge documents.

    Responsibilities:
    - Discover supported Markdown files.
    - Load Markdown content.
    - Parse YAML front matter.
    - Build KnowledgeMetadata from front matter.
    - Generate the deterministic document ID.

    This adapter does NOT:
    - chunk documents
    - generate embeddings
    - perform retrieval
    - communicate with Qdrant
    """

    SUPPORTED_SUFFIXES = {".md", ".markdown"}

    FRONT_MATTER_DELIMITER = "---"

    def list_documents(self, root: Path) -> list[Path]:
        """
        Recursively discover all supported Markdown documents.

        Files are returned in deterministic path order.
        """

        root = Path(root)

        if not root.exists():
            raise FileNotFoundError(
                f"Knowledge root directory does not exist: {root}"
            )

        if not root.is_dir():
            raise NotADirectoryError(
                f"Knowledge root is not a directory: {root}"
            )

        documents = [
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix.lower() in self.SUPPORTED_SUFFIXES
        ]

        return sorted(
            documents,
            key=lambda path: str(path).lower(),
        )

    def load(self, path: Path) -> KnowledgeDocument:
        """
        Load a Markdown knowledge document.

        The document MUST begin with YAML front matter:

            ---
            document_id: outlook-synchronization
            title: Outlook Synchronization Troubleshooting
            category: email
            subcategory: outlook
            version: "1"
            language: en
            access_level: internal
            tags:
              - outlook
              - email
            ---

            # Outlook Synchronization Troubleshooting

            ...

        Front matter is parsed into KnowledgeMetadata and is therefore
        persisted through the chunking and Qdrant ingestion pipeline.
        """

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Knowledge document does not exist: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Knowledge document path is not a file: {path}"
            )

        if path.suffix.lower() not in self.SUPPORTED_SUFFIXES:
            raise ValueError(
                f"Unsupported knowledge document type: {path.suffix}"
            )

        raw = path.read_text(
            encoding="utf-8",
        )

        metadata_values, content = self._parse_front_matter(
            raw,
            path,
        )

        if not content.strip():
            raise ValueError(
                f"Knowledge document content is empty: {path}"
            )

        metadata = self._build_metadata(
            path=path,
            values=metadata_values,
        )

        document_id = deterministic_document_id(
            metadata.document_id,
        )

        return KnowledgeDocument(
            id=document_id,
            content=content,
            metadata=metadata,
        )

    # ==================================================================
    # YAML front matter
    # ==================================================================

    @classmethod
    def _parse_front_matter(
        cls,
        raw: str,
        path: Path,
    ) -> tuple[dict[str, Any], str]:
        """
        Parse YAML front matter from a Markdown document.

        Expected structure:

            ---
            key: value
            ---
            markdown content

        Returns:

            (
                metadata_dictionary,
                markdown_content_without_front_matter,
            )

        The front matter MUST be the first non-BOM content in the file.
        """

        if raw.startswith("\ufeff"):
            raw = raw.lstrip("\ufeff")

        lines = raw.splitlines()

        if not lines:
            raise ValueError(
                f"Knowledge document is empty: {path}"
            )

        # The first line must be the YAML front-matter delimiter.
        if lines[0].strip() != cls.FRONT_MATTER_DELIMITER:
            raise ValueError(
                "Knowledge document must start with YAML front matter: "
                f"{path}"
            )

        closing_index: int | None = None

        for index in range(1, len(lines)):
            if lines[index].strip() == cls.FRONT_MATTER_DELIMITER:
                closing_index = index
                break

        if closing_index is None:
            raise ValueError(
                "Knowledge document YAML front matter is not closed: "
                f"{path}"
            )

        front_matter_text = "\n".join(
            lines[1:closing_index]
        ).strip()

        if not front_matter_text:
            raise ValueError(
                f"Knowledge document front matter is empty: {path}"
            )

        try:
            parsed = yaml.safe_load(front_matter_text)
        except yaml.YAMLError as exc:
            raise ValueError(
                f"Invalid YAML front matter in knowledge document: {path}"
            ) from exc

        if parsed is None:
            raise ValueError(
                f"Knowledge document front matter is empty: {path}"
            )

        if not isinstance(parsed, dict):
            raise ValueError(
                "Knowledge document front matter must be a YAML mapping: "
                f"{path}"
            )

        content = "\n".join(
            lines[closing_index + 1 :]
        ).lstrip("\r\n")

        return dict(parsed), content

    # ==================================================================
    # Metadata
    # ==================================================================

    def _build_metadata(
        self,
        *,
        path: Path,
        values: dict[str, Any],
    ) -> KnowledgeMetadata:
        """
        Build domain metadata from YAML front matter.

        Front matter is authoritative for knowledge taxonomy.

        Required:
        - category

        Recommended:
        - document_id
        - title
        - subcategory
        - version
        - language
        - access_level
        - tags

        Safe defaults are provided for fields where the domain model
        permits them.
        """

        category = self._required_string(
            values,
            "category",
            path,
        )

        subcategory = self._optional_string(
            values,
            "subcategory",
        )

        title = self._optional_string(
            values,
            "title",
        )

        document_id = self._optional_string(
            values,
            "document_id",
        )

        version = self._optional_string(
            values,
            "version",
        ) or "1"

        language = self._optional_string(
            values,
            "language",
        ) or "en"

        access_level = self._optional_string(
            values,
            "access_level",
        ) or "internal"

        tags = self._build_tags(
            path=path,
            values=values,
        )

        if not title:
            title = (
                path.stem
                .replace("-", " ")
                .replace("_", " ")
                .strip()
            )

        if not title:
            title = path.name

        if not document_id:
            document_id = self._document_id_from_path(path)

        return KnowledgeMetadata(
            source_type="markdown",
            category=category,
            subcategory=subcategory,
            title=title,
            document_id=document_id,
            version=version,
            language=language,
            access_level=access_level,
            tags=tags,
        )

    # ==================================================================
    # Metadata helpers
    # ==================================================================

    @staticmethod
    def _required_string(
        values: dict[str, Any],
        key: str,
        path: Path,
    ) -> str:
        """
        Read a required non-empty string metadata field.
        """

        value = values.get(key)

        if value is None:
            raise ValueError(
                f"Knowledge document is missing required front matter "
                f"field '{key}': {path}"
            )

        if not isinstance(value, str):
            raise ValueError(
                f"Knowledge document front matter field '{key}' "
                f"must be a string: {path}"
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"Knowledge document front matter field '{key}' "
                f"cannot be empty: {path}"
            )

        return value

    @staticmethod
    def _optional_string(
        values: dict[str, Any],
        key: str,
    ) -> str | None:
        """
        Read an optional string metadata field.

        Empty strings are treated as missing.
        """

        value = values.get(key)

        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                f"Knowledge document front matter field "
                f"'{key}' must be a string."
            )

        value = value.strip()

        return value or None

    @staticmethod
    def _build_tags(
        *,
        path: Path,
        values: dict[str, Any],
    ) -> list[str]:
        """
        Build normalized knowledge tags.

        Front-matter tags are authoritative when provided.

        The category and subcategory are also included as tags when
        they are not already present. This helps lexical retrieval
        without changing the actual metadata taxonomy.
        """

        raw_tags = values.get("tags", [])

        if raw_tags is None:
            raw_tags = []

        if isinstance(raw_tags, str):
            raw_tags = [raw_tags]

        if not isinstance(raw_tags, list):
            raise ValueError(
                "Knowledge document front matter field 'tags' "
                f"must be a list of strings: {path}"
            )

        tags: list[str] = []

        for tag in raw_tags:
            if not isinstance(tag, str):
                raise ValueError(
                    "Every knowledge document tag must be a string: "
                    f"{path}"
                )

            normalized = tag.strip()

            if normalized and normalized not in tags:
                tags.append(normalized)

        category = values.get("category")

        if isinstance(category, str):
            category = category.strip()

            if category and category not in tags:
                tags.append(category)

        subcategory = values.get("subcategory")

        if isinstance(subcategory, str):
            subcategory = subcategory.strip()

            if subcategory and subcategory not in tags:
                tags.append(subcategory)

        return tags

    # ==================================================================
    # Deterministic document identity
    # ==================================================================

    @staticmethod
    def _document_id_from_path(path: Path) -> str:
        """
        Create the logical document identifier from the file path.

        The UUID/deterministic transformation itself is handled by
        deterministic_document_id() from the domain layer.

        The relative/logical path is preferred over the absolute
        machine-specific path so that document identity remains stable
        across environments.
        """

        normalized = path.as_posix().strip()

        if not normalized:
            raise ValueError(
                f"Cannot derive document identity from path: {path}"
            )

        return normalized
