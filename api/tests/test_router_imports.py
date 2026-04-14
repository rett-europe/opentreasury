"""Tests for the /api/imports router."""

from io import BytesIO
from unittest.mock import AsyncMock

import pytest
from openpyxl import Workbook

from app.main import app
from app.services.dependencies import get_import_service

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

SAMPLE_SUMMARY = {
    "importBatchId": "batch-001",
    "importMode": "full",
    "importSource": "excel-full",
    "accountId": "acc-1",
    "accountLabel": "Unicaja 0382",
    "categoriesCreated": 2,
    "subcategoriesAdded": 3,
    "transactionsImported": 5,
    "duplicatesSkipped": 1,
    "rowsSkipped": 0,
    "warnings": [],
}

SAMPLE_PREVIEW = {
    "valid": True,
    "importMode": "full",
    "errors": [],
    "warnings": [],
    "totalRows": 10,
    "rowsWithErrors": 0,
    "account": {"exists": True, "id": "acc-1", "label": "Unicaja 0382", "iban": "ES70..."},
    "newCategories": [{"name": "Donations", "type": "income"}],
    "newSubcategories": [{"categoryName": "Donations", "name": "Individual"}],
    "transactionsToImport": 8,
    "duplicatesToSkip": 2,
}

SAMPLE_PREVIEW_INVALID = {
    "valid": False,
    "importMode": "full",
    "errors": ["3 row(s) have empty date field", "1 row(s) have unparseable amounts"],
    "warnings": [],
    "totalRows": 10,
    "rowsWithErrors": 4,
    "account": {"exists": True, "id": "acc-1", "label": "Unicaja 0382", "iban": "ES70..."},
    "newCategories": [],
    "newSubcategories": [],
    "transactionsToImport": 0,
    "duplicatesToSkip": 0,
}


def make_minimal_xlsx() -> bytes:
    """Create a minimal valid .xlsx file for testing."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Test"
    ws.append(["data"])
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def mock_import_svc():
    svc = AsyncMock()
    svc.import_workbook.return_value = SAMPLE_SUMMARY
    svc.preview_workbook.return_value = SAMPLE_PREVIEW
    return svc


# ---------------------------------------------------------------------------
# POST /api/imports/preview?accountId=xxx
# ---------------------------------------------------------------------------


class TestPreviewImport:
    async def test_valid_preview(self, admin_client, mock_import_svc):
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        response = await admin_client.post(
            "/api/imports/preview?accountId=acc-1",
            files={"file": ("import.xlsx", make_minimal_xlsx(), XLSX_CONTENT_TYPE)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["transactionsToImport"] == 8
        assert data["duplicatesToSkip"] == 2
        assert len(data["newCategories"]) == 1
        mock_import_svc.preview_workbook.assert_awaited_once()

    async def test_invalid_preview(self, admin_client, mock_import_svc):
        mock_import_svc.preview_workbook.return_value = SAMPLE_PREVIEW_INVALID
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        response = await admin_client.post(
            "/api/imports/preview?accountId=acc-1",
            files={"file": ("import.xlsx", make_minimal_xlsx(), XLSX_CONTENT_TYPE)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) == 2

    async def test_preview_missing_account_id(self, admin_client, mock_import_svc):
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        response = await admin_client.post(
            "/api/imports/preview",
            files={"file": ("import.xlsx", make_minimal_xlsx(), XLSX_CONTENT_TYPE)},
        )

        assert response.status_code == 422

    async def test_preview_account_not_found(self, admin_client, mock_import_svc):
        mock_import_svc.preview_workbook.side_effect = ValueError("Account 'acc-bad' not found or inactive")
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        response = await admin_client.post(
            "/api/imports/preview?accountId=acc-bad",
            files={"file": ("import.xlsx", make_minimal_xlsx(), XLSX_CONTENT_TYPE)},
        )

        assert response.status_code == 404

    async def test_preview_empty_body(self, admin_client, mock_import_svc):
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        response = await admin_client.post(
            "/api/imports/preview?accountId=acc-1",
            files={"file": ("import.xlsx", b"", XLSX_CONTENT_TYPE)},
        )

        assert response.status_code == 400

    async def test_viewer_cannot_preview(self, viewer_client, mock_import_svc):
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        response = await viewer_client.post(
            "/api/imports/preview?accountId=acc-1",
            files={"file": ("import.xlsx", make_minimal_xlsx(), XLSX_CONTENT_TYPE)},
        )

        assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/imports/workbook?accountId=xxx (multipart: file + metadata)
# ---------------------------------------------------------------------------


class TestImportWorkbook:
    async def test_successful_import(self, admin_client, mock_import_svc):
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        response = await admin_client.post(
            "/api/imports/workbook?accountId=acc-1",
            files={"file": ("import.xlsx", make_minimal_xlsx(), XLSX_CONTENT_TYPE)},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["accountId"] == "acc-1"
        assert data["importBatchId"] == "batch-001"
        assert data["importMode"] == "full"
        assert data["importSource"] == "excel-full"
        assert data["transactionsImported"] == 5
        assert data["duplicatesSkipped"] == 1
        mock_import_svc.import_workbook.assert_awaited_once()

    async def test_import_with_category_overrides(self, admin_client, mock_import_svc):
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        response = await admin_client.post(
            "/api/imports/workbook?accountId=acc-1",
            files={"file": ("import.xlsx", make_minimal_xlsx(), XLSX_CONTENT_TYPE)},
            data={"metadata": '{"categoryTypeOverrides": {"Cuotas": "income", "Donaciones": "income"}}'},
        )

        assert response.status_code == 201
        call_kwargs = mock_import_svc.import_workbook.call_args.kwargs
        assert call_kwargs["category_type_overrides"] == {"Cuotas": "income", "Donaciones": "income"}

    async def test_import_missing_account_id(self, admin_client, mock_import_svc):
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        response = await admin_client.post(
            "/api/imports/workbook",
            files={"file": ("import.xlsx", make_minimal_xlsx(), XLSX_CONTENT_TYPE)},
        )

        assert response.status_code == 422

    async def test_empty_body_returns_400(self, admin_client, mock_import_svc):
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        response = await admin_client.post(
            "/api/imports/workbook?accountId=acc-1",
            files={"file": ("import.xlsx", b"", XLSX_CONTENT_TYPE)},
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    async def test_file_too_large_returns_413(self, admin_client, mock_import_svc):
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        oversized = b"\x00" * (11 * 1024 * 1024)

        response = await admin_client.post(
            "/api/imports/workbook?accountId=acc-1",
            files={"file": ("import.xlsx", oversized, XLSX_CONTENT_TYPE)},
        )

        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

    async def test_invalid_workbook_returns_400(self, admin_client, mock_import_svc):
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc
        mock_import_svc.import_workbook.side_effect = ValueError("No movement sheet found in workbook")

        response = await admin_client.post(
            "/api/imports/workbook?accountId=acc-1",
            files={"file": ("import.xlsx", make_minimal_xlsx(), XLSX_CONTENT_TYPE)},
        )

        assert response.status_code == 400
        assert "movement sheet" in response.json()["detail"].lower()

    async def test_viewer_cannot_import(self, viewer_client, mock_import_svc):
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        response = await viewer_client.post(
            "/api/imports/workbook?accountId=acc-1",
            files={"file": ("import.xlsx", make_minimal_xlsx(), XLSX_CONTENT_TYPE)},
        )

        assert response.status_code == 403

    async def test_old_endpoint_returns_404(self, admin_client, mock_import_svc):
        """Old /unicaja-template endpoint should no longer exist."""
        app.dependency_overrides[get_import_service] = lambda: mock_import_svc

        response = await admin_client.post(
            "/api/imports/unicaja-template?accountId=acc-1",
            files={"file": ("import.xlsx", make_minimal_xlsx(), XLSX_CONTENT_TYPE)},
        )

        assert response.status_code in (404, 405)
