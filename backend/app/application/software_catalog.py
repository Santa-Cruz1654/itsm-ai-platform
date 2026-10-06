from __future__ import annotations

from app.domain.software import (
    SoftwareCatalogItem,
)


class SoftwareCatalog:
    """
    Deterministic enterprise software catalogue.

    This is intentionally not LLM-driven.

    The AI identifies the requested software.
    The catalogue determines whether that software is approved
    for this workflow.
    """

    def __init__(
        self,
        items: list[SoftwareCatalogItem] | None = None,
    ) -> None:
        self._items = (
            items
            if items is not None
            else self._default_items()
        )

        self._by_name: dict[
            str,
            SoftwareCatalogItem,
        ] = {}

        self._index_items()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(
        self,
        software_name: str,
    ) -> SoftwareCatalogItem | None:
        """
        Resolve a software request by name or approved alias.
        """

        normalized = self._normalize(
            software_name,
        )

        if not normalized:
            return None

        return self._by_name.get(
            normalized,
        )

    def list_items(
        self,
    ) -> list[SoftwareCatalogItem]:
        """
        Return all approved catalogue items.
        """

        return list(self._items)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _index_items(self) -> None:
        for item in self._items:
            self._by_name[
                self._normalize(item.name)
            ] = item

            for alias in item.aliases:
                self._by_name[
                    self._normalize(alias)
                ] = item

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        return " ".join(
            value.strip().lower().split()
        )

    @staticmethod
    def _default_items() -> list[
        SoftwareCatalogItem
    ]:
        return [
            SoftwareCatalogItem(
                catalog_id="SW-VSCODE",
                name="Visual Studio Code",
                version="latest-approved",
                category="development",
                description=(
                    "Microsoft Visual Studio Code "
                    "development environment."
                ),
                aliases=[
                    "VS Code",
                    "Visual Studio Code",
                    "Code",
                ],
            ),
            SoftwareCatalogItem(
                catalog_id="SW-GIT",
                name="Git",
                version="latest-approved",
                category="development",
                description=(
                    "Git distributed version control client."
                ),
                aliases=[
                    "Git SCM",
                ],
            ),
            SoftwareCatalogItem(
                catalog_id="SW-POSTMAN",
                name="Postman",
                version="latest-approved",
                category="development",
                description=(
                    "Postman API development and testing client."
                ),
                aliases=[],
            ),
            SoftwareCatalogItem(
                catalog_id="SW-7ZIP",
                name="7-Zip",
                version="latest-approved",
                category="utilities",
                description=(
                    "7-Zip archive and compression utility."
                ),
                aliases=[
                    "7zip",
                ],
            ),
            SoftwareCatalogItem(
                catalog_id="SW-NPP",
                name="Notepad++",
                version="latest-approved",
                category="utilities",
                description=(
                    "Notepad++ text and source-code editor."
                ),
                aliases=[
                    "Notepad Plus Plus",
                ],
            ),
        ]