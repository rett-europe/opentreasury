"""Tests for CategoryService — business logic with mocked repository."""

from unittest.mock import AsyncMock

import pytest

from app.models.domain import AuditAction, CategoryType
from app.models.schemas import CategoryCreate, CategoryUpdate, SubcategoryCreate, SubcategoryUpdate
from app.services.category_service import CategoryService

from .conftest import make_category

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_audit():
    return AsyncMock()


@pytest.fixture
def mock_txn_repo():
    repo = AsyncMock()
    repo.count_by_category.return_value = 0
    return repo


@pytest.fixture
def service(mock_repo, mock_audit, mock_txn_repo):
    return CategoryService(repo=mock_repo, audit_service=mock_audit, transaction_repo=mock_txn_repo)


USER_ID = "test-user-oid-abc123"
USER_NAME = "Test User"


# ---------------------------------------------------------------------------
# list_categories
# ---------------------------------------------------------------------------


class TestListCategories:
    async def test_delegates_to_repo(self, service, mock_repo):
        cats = [make_category(), make_category(id="cat-002", name="Expenses")]
        mock_repo.list_all.return_value = cats

        result = await service.list_categories()

        assert result == cats
        mock_repo.list_all.assert_awaited_once()


# ---------------------------------------------------------------------------
# create_category
# ---------------------------------------------------------------------------


class TestCreateCategory:
    async def test_with_subcategories(self, service, mock_repo, mock_audit):
        data = CategoryCreate(
            name="Donations",
            description="Income from donors",
            category_type=CategoryType.INCOME,
            sort_order=1,
            subcategories=[
                SubcategoryCreate(name="Individual"),
                SubcategoryCreate(name="Corporate"),
            ],
        )
        mock_repo.create.return_value = {"id": "cat-new", "name": "Donations"}

        result = await service.create_category(data, USER_ID, USER_NAME)

        assert result["name"] == "Donations"

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["type"] == "category"
        assert call_args["name"] == "Donations"
        assert call_args["isActive"] is True
        assert len(call_args["subcategories"]) == 2
        assert call_args["subcategories"][0]["name"] == "Individual"
        assert call_args["subcategories"][0]["isActive"] is True
        assert call_args["subcategories"][1]["name"] == "Corporate"
        # Each subcategory should have a UUID id
        assert call_args["subcategories"][0]["id"] is not None
        assert call_args["subcategories"][1]["id"] is not None

    async def test_empty_subcategories(self, service, mock_repo, mock_audit):
        data = CategoryCreate(name="Misc", category_type=CategoryType.EXPENSE, sort_order=99)
        mock_repo.create.return_value = {"id": "cat-new", "name": "Misc"}

        await service.create_category(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["subcategories"] == []

    async def test_calls_audit(self, service, mock_repo, mock_audit):
        data = CategoryCreate(name="Donations", category_type=CategoryType.INCOME, sort_order=1)
        mock_repo.create.return_value = {"id": "cat-new"}

        await service.create_category(data, USER_ID, USER_NAME)

        mock_audit.log.assert_awaited_once()
        audit_call = mock_audit.log.call_args
        assert audit_call.kwargs["entity_type"] == "Category"
        assert audit_call.kwargs["action"] == AuditAction.CREATE
        assert audit_call.kwargs["new_values"] == {"name": "Donations"}


# ---------------------------------------------------------------------------
# add_subcategory
# ---------------------------------------------------------------------------


class TestAddSubcategory:
    async def test_appends_to_existing(self, service, mock_repo, mock_audit):
        existing = make_category()
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = existing

        data = SubcategoryCreate(name="Other Donors")

        result = await service.add_subcategory("cat-001", data, USER_ID, USER_NAME)

        assert result is not None
        replace_doc = mock_repo.replace.call_args[0][1]
        assert len(replace_doc["subcategories"]) == 3  # 2 original + 1 new
        new_sub = replace_doc["subcategories"][-1]
        assert new_sub["name"] == "Other Donors"
        assert new_sub["isActive"] is True

    async def test_category_not_found(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = None

        data = SubcategoryCreate(name="Orphan Sub")

        result = await service.add_subcategory("cat-nonexistent", data, USER_ID, USER_NAME)

        assert result is None
        mock_repo.replace.assert_not_awaited()


# ---------------------------------------------------------------------------
# update_subcategory
# ---------------------------------------------------------------------------


class TestUpdateSubcategory:
    async def test_finds_and_updates_correct_sub(self, service, mock_repo, mock_audit):
        existing = make_category()
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = existing

        data = SubcategoryUpdate(name="Updated Donors", is_active=False)

        result = await service.update_subcategory("cat-001", "subcat-001", data, USER_ID, USER_NAME)

        assert result is not None
        replace_doc = mock_repo.replace.call_args[0][1]
        updated_sub = next(s for s in replace_doc["subcategories"] if s["id"] == "subcat-001")
        assert updated_sub["name"] == "Updated Donors"
        assert updated_sub["isActive"] is False

    async def test_subcategory_not_found(self, service, mock_repo, mock_audit):
        existing = make_category()
        mock_repo.get_by_id.return_value = existing

        data = SubcategoryUpdate(name="Ghost")

        result = await service.update_subcategory("cat-001", "subcat-nonexistent", data, USER_ID, USER_NAME)

        assert result is None

    async def test_category_not_found(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = None

        data = SubcategoryUpdate(name="Ghost")

        result = await service.update_subcategory("cat-nonexistent", "subcat-001", data, USER_ID, USER_NAME)

        assert result is None


# ---------------------------------------------------------------------------
# remove_subcategory
# ---------------------------------------------------------------------------


class TestRemoveSubcategory:
    async def test_removes_from_list(self, service, mock_repo, mock_audit):
        existing = make_category()
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = existing

        result = await service.remove_subcategory("cat-001", "subcat-001", USER_ID, USER_NAME)

        assert result is not None
        replace_doc = mock_repo.replace.call_args[0][1]
        assert len(replace_doc["subcategories"]) == 1
        assert replace_doc["subcategories"][0]["id"] == "subcat-002"

        mock_audit.log.assert_awaited_once()
        audit_call = mock_audit.log.call_args
        assert audit_call.kwargs["old_values"] == {"removedSubcategoryId": "subcat-001"}

    async def test_not_found_returns_none(self, service, mock_repo, mock_audit):
        existing = make_category()
        mock_repo.get_by_id.return_value = existing

        result = await service.remove_subcategory("cat-001", "subcat-nonexistent", USER_ID, USER_NAME)

        assert result is None
        mock_repo.replace.assert_not_awaited()

    async def test_category_not_found(self, service, mock_repo, mock_audit):
        mock_repo.get_by_id.return_value = None

        result = await service.remove_subcategory("cat-nonexistent", "subcat-001", USER_ID, USER_NAME)

        assert result is None


# ---------------------------------------------------------------------------
# categoryType field
# ---------------------------------------------------------------------------


class TestCategoryType:
    async def test_create_stores_category_type(self, service, mock_repo, mock_audit):
        """categoryType is stored in the document."""
        data = CategoryCreate(name="Income Category", category_type=CategoryType.INCOME, sort_order=1)
        mock_repo.create.return_value = {"id": "cat-new", "name": "Income Category", "categoryType": "income"}

        await service.create_category(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["categoryType"] == "income"

    async def test_create_stores_expense_type(self, service, mock_repo, mock_audit):
        """Expense categoryType is stored correctly."""
        data = CategoryCreate(name="Expense Category", category_type=CategoryType.EXPENSE, sort_order=2)
        mock_repo.create.return_value = {"id": "cat-new", "name": "Expense Category", "categoryType": "expense"}

        await service.create_category(data, USER_ID, USER_NAME)

        call_args = mock_repo.create.call_args[0][0]
        assert call_args["categoryType"] == "expense"

    async def test_update_category_type(self, service, mock_repo, mock_audit):
        """categoryType can be updated."""
        existing = make_category(id="cat-001", categoryType="income")
        mock_repo.get_by_id.return_value = existing
        mock_repo.replace.return_value = {**existing, "categoryType": "expense"}

        data = CategoryUpdate(category_type=CategoryType.EXPENSE)

        result = await service.update_category("cat-001", data, USER_ID, USER_NAME)

        assert result is not None
        replace_doc = mock_repo.replace.call_args[0][1]
        assert replace_doc["categoryType"] == "expense"

        # Verify audit tracks the change
        mock_audit.log.assert_awaited_once()
        audit_call = mock_audit.log.call_args
        assert audit_call.kwargs["old_values"] == {"categoryType": "income"}
        assert audit_call.kwargs["new_values"] == {"categoryType": "expense"}
