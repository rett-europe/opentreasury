"""
Integration tests using the generated fixture workbooks.
Validates that preview_workbook produces the correct verdict for each scenario.
"""

from pathlib import Path
from unittest.mock import AsyncMock

from app.services.import_service import ImportService

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Shared mock account for "existing account" scenarios
EXISTING_ACCOUNT = {
    "id": "acc-1",
    "accountLabel": "Unicaja 0382",
    "iban": "ES0000490001000000001234",
    "bankNameShort": "Unicaja",
}


async def build_service(*, account=None, categories=None, transactions=None):
    account_svc = AsyncMock()
    category_svc = AsyncMock()
    txn_svc = AsyncMock()

    account_svc.get_account.return_value = account or EXISTING_ACCOUNT
    category_svc.list_categories.return_value = categories or []
    txn_svc.get_transactions_for_export.return_value = transactions or []

    return ImportService(
        account_service=account_svc,
        category_service=category_svc,
        transaction_service=txn_svc,
    )


def load_fixture(name: str) -> bytes:
    path = FIXTURES_DIR / name
    assert path.exists(), f"Fixture not found: {path}. Run generate_import_fixtures.py first."
    return path.read_bytes()


class TestFixtureValidSpanish:
    async def test_preview_valid(self):
        svc = await build_service(account=EXISTING_ACCOUNT)
        result = await svc.preview_workbook(load_fixture("valid-spanish.xlsx"), account_id="acc-1")

        assert result["valid"] is True
        assert result["errors"] == []
        assert result["transactionsToImport"] == 5
        assert result["duplicatesToSkip"] == 0
        assert len(result["newCategories"]) == 3
        assert result["account"]["id"] == "acc-1"


class TestFixtureValidEnglish:
    async def test_preview_valid(self):
        svc = await build_service(account=EXISTING_ACCOUNT)
        result = await svc.preview_workbook(load_fixture("valid-english.xlsx"), account_id="acc-1")

        assert result["valid"] is True
        assert result["transactionsToImport"] == 5
        assert len(result["newCategories"]) == 3


class TestFixtureWithDuplicates:
    async def test_preview_shows_duplicates(self):
        existing_txns = [
            {
                "date": "2025-01-02",
                "bankDescription": "BULTO MILLET VICTOR",
                "detail": "transferencia",
                "amount": 30,
            },
            {
                "date": "2025-01-03",
                "bankDescription": "FRANCISCO BORJA",
                "detail": "particular",
                "amount": 10,
            },
        ]
        svc = await build_service(account=EXISTING_ACCOUNT, transactions=existing_txns)
        result = await svc.preview_workbook(load_fixture("with-duplicates.xlsx"), account_id="acc-1")

        assert result["valid"] is True
        assert result["duplicatesToSkip"] == 2
        assert result["transactionsToImport"] == 1


class TestFixtureDataErrors:
    async def test_preview_rejects(self):
        svc = await build_service()
        result = await svc.preview_workbook(load_fixture("data-errors.xlsx"), account_id="acc-1")

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        error_text = " ".join(result["errors"]).lower()
        assert "empty date" in error_text
        assert "empty amount" in error_text
        assert "could not be read" in error_text
        assert "empty category" in error_text
        assert "empty subcategory" in error_text


class TestFixtureOrphanedSubcategory:
    async def test_preview_rejects(self):
        svc = await build_service()
        result = await svc.preview_workbook(load_fixture("orphaned-subcategory.xlsx"), account_id="acc-1")

        assert result["valid"] is False
        error_text = " ".join(result["errors"]).lower()
        assert "mystery subcategory" in error_text
        assert "unknown category" in error_text


class TestFixtureMissingCategoriesSheet:
    async def test_preview_inline_mode(self):
        """Phase 2: file with category columns but no categories sheet → Inline mode (valid)."""
        svc = await build_service()
        result = await svc.preview_workbook(load_fixture("missing-categories-sheet.xlsx"), account_id="acc-1")

        assert result["valid"] is True
        assert result["importMode"] == "inline"


class TestFixtureMissingHeaders:
    async def test_preview_detects_bank_mode(self):
        """missing-headers.xlsx has Date + Amount but no Category columns → Bank mode (valid)."""
        svc = await build_service()
        result = await svc.preview_workbook(load_fixture("missing-headers.xlsx"), account_id="acc-1")

        assert result["valid"] is True
        assert result["importMode"] == "bank"


class TestFixtureEmptyRows:
    async def test_preview_rejects(self):
        svc = await build_service()
        result = await svc.preview_workbook(load_fixture("empty-rows.xlsx"), account_id="acc-1")

        assert result["valid"] is False
        assert any("no data rows" in e.lower() for e in result["errors"])


class TestFixtureNewAccount:
    async def test_preview_shows_selected_account(self):
        svc = await build_service()
        result = await svc.preview_workbook(load_fixture("new-account.xlsx"), account_id="acc-1")

        assert result["valid"] is True
        assert result["account"]["id"] == "acc-1"
        assert result["transactionsToImport"] == 2
