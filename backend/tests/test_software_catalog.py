from app.application.software_catalog import (
    SoftwareCatalog,
)


def test_visual_studio_code_is_in_catalogue() -> None:
    catalog = SoftwareCatalog()

    item = catalog.get(
        "Visual Studio Code",
    )

    assert item is not None
    assert item.name == (
        "Visual Studio Code"
    )
    assert item.catalog_id == (
        "SW-VSCODE"
    )
    assert item.provisioning_supported is True


def test_visual_studio_code_alias_resolves() -> None:
    catalog = SoftwareCatalog()

    item = catalog.get(
        "VS Code",
    )

    assert item is not None
    assert item.name == (
        "Visual Studio Code"
    )


def test_catalogue_lookup_is_case_insensitive() -> None:
    catalog = SoftwareCatalog()

    item = catalog.get(
        "visual studio code",
    )

    assert item is not None
    assert item.name == (
        "Visual Studio Code"
    )


def test_unknown_software_is_not_approved() -> None:
    catalog = SoftwareCatalog()

    item = catalog.get(
        "Random Enterprise Tool",
    )

    assert item is None


def test_catalogue_contains_multiple_approved_items() -> None:
    catalog = SoftwareCatalog()

    items = catalog.list_items()

    assert len(items) >= 5

    names = {
        item.name
        for item in items
    }

    assert (
        "Visual Studio Code"
        in names
    )