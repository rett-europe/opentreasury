"""Tests for SplitService — split transaction business logic with mocked repository."""

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.services.split_service import SplitService

from .conftest import make_transaction

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

USER_ID = "test-user-oid-abc123"
USER_NAME = "Test User"


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_audit():
    return AsyncMock()


@pytest.fixture
def mock_category_repo():
    repo = AsyncMock()
    repo.get_by_id.return_value = {
        "id": "cat-001",
        "categoryType": "income",
        "name": "Donations",
        "isActive": True,
        "subcategories": [
            {"id": "subcat-001", "name": "Individual Donors", "isActive": True},
            {"id": "subcat-002", "name": "Corporate Sponsors", "isActive": True},
        ],
    }
    return repo


@pytest.fixture
def service(mock_repo, mock_audit, mock_category_repo):
    return SplitService(
        repo=mock_repo,
        audit_service=mock_audit,
        category_repo=mock_category_repo,
    )


def _make_split_lines(amounts, category_ids=None, subcategory_ids=None, tag_ids_list=None, details=None):
    """Helper to build a list of split line dicts (as the service would receive).

    Amounts are provided as unsigned Decimals; the service should apply the
    parent sign.  This helper returns dicts matching SplitLineCreate shape.
    """
    lines = []
    for i, amt in enumerate(amounts):
        line = {"amount": amt}
        if category_ids and i < len(category_ids):
            line["categoryId"] = category_ids[i]
        if subcategory_ids and i < len(subcategory_ids):
            line["subcategoryId"] = subcategory_ids[i]
        if tag_ids_list and i < len(tag_ids_list):
            line["tagIds"] = tag_ids_list[i]
        if details and i < len(details):
            line["detail"] = details[i]
        lines.append(line)
    return lines


# ---------------------------------------------------------------------------
# Happy path — create split
# ---------------------------------------------------------------------------


class TestCreateSplit:
    """Tests for creating a split on a non-split transaction."""

    async def test_split_into_two_lines_minimum(self, service, mock_repo, mock_audit):
        """Split a transaction into exactly 2 lines (minimum allowed)."""
        parent = make_transaction(
            id="tx-001",
            amount=Decimal("-150.00"),
            transactionType="expense",
            categoryId="cat-existing",
            subcategoryId="subcat-existing",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True, "splitCount": 2}

        lines = _make_split_lines(
            amounts=[Decimal("100.00"), Decimal("50.00")],
        )

        result = await service.split_transaction(
            transaction_id="tx-001",
            year=2026,
            month=4,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        assert result is not None
        mock_repo.replace.assert_awaited_once()
        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc["isSplit"] is True
        assert saved_doc["splitCount"] == 2
        assert len(saved_doc["splitLines"]) == 2

    async def test_split_into_multiple_lines(self, service, mock_repo, mock_audit):
        """Split a transaction into 5+ lines."""
        parent = make_transaction(
            id="tx-002",
            amount=Decimal("3600.00"),
            transactionType="income",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True, "splitCount": 5}

        lines = _make_split_lines(
            amounts=[
                Decimal("1000.00"),
                Decimal("800.00"),
                Decimal("700.00"),
                Decimal("600.00"),
                Decimal("500.00"),
            ],
        )

        result = await service.split_transaction(
            transaction_id="tx-002",
            year=2026,
            month=3,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        assert result is not None
        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc["splitCount"] == 5
        assert len(saved_doc["splitLines"]) == 5

    async def test_split_with_categories_on_all_lines(self, service, mock_repo, mock_audit, mock_category_repo):
        """Each split line can have a category."""
        parent = make_transaction(
            id="tx-003",
            amount=Decimal("-850.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        mock_category_repo.get_by_id.return_value = {
            "id": "cat-exp",
            "categoryType": "expense",
            "isActive": True,
            "subcategories": [
                {"id": "subcat-a", "name": "A", "isActive": True},
            ],
        }

        lines = _make_split_lines(
            amounts=[Decimal("600.00"), Decimal("200.00"), Decimal("50.00")],
            category_ids=["cat-exp", "cat-exp", "cat-exp"],
            subcategory_ids=["subcat-a", None, None],
        )

        result = await service.split_transaction(
            transaction_id="tx-003",
            year=2026,
            month=3,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        assert result is not None
        saved_doc = mock_repo.replace.call_args[0][1]
        assert all(sl.get("categoryId") == "cat-exp" for sl in saved_doc["splitLines"])

    async def test_split_with_mixed_categorized_and_uncategorized(
        self, service, mock_repo, mock_audit, mock_category_repo
    ):
        """Some lines have categories, some don't."""
        parent = make_transaction(
            id="tx-004",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        mock_category_repo.get_by_id.return_value = {
            "id": "cat-exp",
            "categoryType": "expense",
            "isActive": True,
            "subcategories": [],
        }

        lines = _make_split_lines(
            amounts=[Decimal("120.00"), Decimal("80.00")],
            category_ids=["cat-exp", None],
        )

        result = await service.split_transaction(
            transaction_id="tx-004",
            year=2026,
            month=4,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        assert result is not None
        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc["splitLines"][0].get("categoryId") == "cat-exp"
        assert saved_doc["splitLines"][1].get("categoryId") is None

    async def test_split_with_tags_and_detail(self, service, mock_repo, mock_audit):
        """Split lines can carry tags and detail text."""
        parent = make_transaction(
            id="tx-005",
            amount=Decimal("600.00"),
            transactionType="income",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        lines = _make_split_lines(
            amounts=[Decimal("300.00"), Decimal("300.00")],
            tag_ids_list=[["tag-2026"], ["tag-2026", "tag-navidad"]],
            details=["García López, Ana", "Martínez Ruiz, Juan"],
        )

        result = await service.split_transaction(
            transaction_id="tx-005",
            year=2026,
            month=3,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        assert result is not None
        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc["splitLines"][0]["detail"] == "García López, Ana"
        assert saved_doc["splitLines"][1]["tagIds"] == ["tag-2026", "tag-navidad"]

    async def test_parent_gets_is_split_and_split_count(self, service, mock_repo, mock_audit):
        """Parent document should have isSplit=True and splitCount set."""
        parent = make_transaction(
            id="tx-006",
            amount=Decimal("-300.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        lines = _make_split_lines(
            amounts=[Decimal("200.00"), Decimal("100.00")],
            category_ids=["cat-a", "cat-b"],
        )

        await service.split_transaction(
            transaction_id="tx-006",
            year=2026,
            month=4,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc["isSplit"] is True
        assert saved_doc["splitCount"] == 2
        assert "cat-a" in saved_doc.get("splitCategoryIds", [])
        assert "cat-b" in saved_doc.get("splitCategoryIds", [])

    async def test_parent_category_cleared_on_split(self, service, mock_repo, mock_audit):
        """Parent categoryId and subcategoryId should be cleared when split."""
        parent = make_transaction(
            id="tx-007",
            amount=Decimal("-500.00"),
            transactionType="expense",
            categoryId="cat-old",
            subcategoryId="subcat-old",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        lines = _make_split_lines(amounts=[Decimal("300.00"), Decimal("200.00")])

        await service.split_transaction(
            transaction_id="tx-007",
            year=2026,
            month=4,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc["categoryId"] is None
        assert saved_doc["subcategoryId"] is None

    async def test_audit_logged_on_create_split(self, service, mock_repo, mock_audit):
        """Creating a split should log an audit entry."""
        parent = make_transaction(
            id="tx-008",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        lines = _make_split_lines(amounts=[Decimal("120.00"), Decimal("80.00")])

        await service.split_transaction(
            transaction_id="tx-008",
            year=2026,
            month=4,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        mock_audit.log.assert_awaited_once()
        audit_kwargs = mock_audit.log.call_args.kwargs
        assert audit_kwargs["entity_type"] == "Transaction"
        assert audit_kwargs["entity_id"] == "tx-008"
        assert audit_kwargs["changed_by"] == USER_ID


# ---------------------------------------------------------------------------
# Happy path — update split
# ---------------------------------------------------------------------------


class TestUpdateSplit:
    """Tests for updating an existing split (PUT)."""

    async def test_update_split_lines(self, service, mock_repo, mock_audit):
        """Update all split lines on an already-split transaction."""
        parent = make_transaction(
            id="tx-010",
            amount=Decimal("-300.00"),
            transactionType="expense",
            isDeleted=False,
            isSplit=True,
            splitCount=2,
            splitLines=[
                {"id": "sl-1", "amount": -200.0, "categoryId": "cat-a", "sortOrder": 1},
                {"id": "sl-2", "amount": -100.0, "categoryId": "cat-b", "sortOrder": 2},
            ],
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "splitCount": 2}

        new_lines = _make_split_lines(
            amounts=[Decimal("150.00"), Decimal("150.00")],
            category_ids=["cat-c", "cat-d"],
        )

        result = await service.update_split(
            transaction_id="tx-010",
            year=2026,
            month=4,
            lines=new_lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        assert result is not None
        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc["splitCount"] == 2
        assert len(saved_doc["splitLines"]) == 2

    async def test_add_more_lines_to_existing_split(self, service, mock_repo, mock_audit):
        """Add more lines to an existing split (increase count)."""
        parent = make_transaction(
            id="tx-011",
            amount=Decimal("-600.00"),
            transactionType="expense",
            isDeleted=False,
            isSplit=True,
            splitCount=2,
            splitLines=[
                {"id": "sl-1", "amount": -400.0, "sortOrder": 1},
                {"id": "sl-2", "amount": -200.0, "sortOrder": 2},
            ],
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "splitCount": 3}

        new_lines = _make_split_lines(
            amounts=[Decimal("300.00"), Decimal("200.00"), Decimal("100.00")],
        )

        result = await service.update_split(
            transaction_id="tx-011",
            year=2026,
            month=4,
            lines=new_lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        assert result is not None
        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc["splitCount"] == 3
        assert len(saved_doc["splitLines"]) == 3

    async def test_remove_lines_from_split_min_two_remain(self, service, mock_repo, mock_audit):
        """Remove lines from an existing split — at least 2 must remain."""
        parent = make_transaction(
            id="tx-012",
            amount=Decimal("-500.00"),
            transactionType="expense",
            isDeleted=False,
            isSplit=True,
            splitCount=4,
            splitLines=[
                {"id": "sl-1", "amount": -200.0, "sortOrder": 1},
                {"id": "sl-2", "amount": -150.0, "sortOrder": 2},
                {"id": "sl-3", "amount": -100.0, "sortOrder": 3},
                {"id": "sl-4", "amount": -50.0, "sortOrder": 4},
            ],
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "splitCount": 2}

        new_lines = _make_split_lines(
            amounts=[Decimal("300.00"), Decimal("200.00")],
        )

        result = await service.update_split(
            transaction_id="tx-012",
            year=2026,
            month=4,
            lines=new_lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        assert result is not None
        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc["splitCount"] == 2

    async def test_change_categories_on_split_lines(self, service, mock_repo, mock_audit):
        """Changing categories on split lines updates splitCategoryIds."""
        parent = make_transaction(
            id="tx-013",
            amount=Decimal("-400.00"),
            transactionType="expense",
            isDeleted=False,
            isSplit=True,
            splitCount=2,
            splitCategoryIds=["cat-a", "cat-b"],
            splitLines=[
                {"id": "sl-1", "amount": -200.0, "categoryId": "cat-a", "sortOrder": 1},
                {"id": "sl-2", "amount": -200.0, "categoryId": "cat-b", "sortOrder": 2},
            ],
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "splitCount": 2}

        new_lines = _make_split_lines(
            amounts=[Decimal("200.00"), Decimal("200.00")],
            category_ids=["cat-c", "cat-d"],
        )

        await service.update_split(
            transaction_id="tx-013",
            year=2026,
            month=4,
            lines=new_lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        saved_doc = mock_repo.replace.call_args[0][1]
        assert "cat-c" in saved_doc.get("splitCategoryIds", [])
        assert "cat-d" in saved_doc.get("splitCategoryIds", [])

    async def test_audit_logged_on_update_split(self, service, mock_repo, mock_audit):
        """Updating a split should log an audit entry."""
        parent = make_transaction(
            id="tx-014",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
            isSplit=True,
            splitCount=2,
            splitLines=[
                {"id": "sl-1", "amount": -100.0, "sortOrder": 1},
                {"id": "sl-2", "amount": -100.0, "sortOrder": 2},
            ],
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = parent

        new_lines = _make_split_lines(
            amounts=[Decimal("120.00"), Decimal("80.00")],
        )

        await service.update_split(
            transaction_id="tx-014",
            year=2026,
            month=4,
            lines=new_lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        mock_audit.log.assert_awaited_once()
        audit_kwargs = mock_audit.log.call_args.kwargs
        assert audit_kwargs["entity_id"] == "tx-014"
        assert audit_kwargs["changed_by"] == USER_ID


# ---------------------------------------------------------------------------
# Happy path — unsplit
# ---------------------------------------------------------------------------


class TestUnsplit:
    """Tests for unsplitting (reverting to single transaction)."""

    async def test_unsplit_removes_split_data(self, service, mock_repo, mock_audit):
        """Unsplit should remove isSplit, splitLines, splitCount."""
        parent = make_transaction(
            id="tx-020",
            amount=Decimal("-300.00"),
            transactionType="expense",
            isDeleted=False,
            isSplit=True,
            splitCount=3,
            splitCategoryIds=["cat-a", "cat-b", "cat-c"],
            splitLines=[
                {"id": "sl-1", "amount": -100.0, "categoryId": "cat-a", "sortOrder": 1},
                {"id": "sl-2", "amount": -100.0, "categoryId": "cat-b", "sortOrder": 2},
                {"id": "sl-3", "amount": -100.0, "categoryId": "cat-c", "sortOrder": 3},
            ],
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": False, "splitLines": []}

        result = await service.unsplit_transaction(
            transaction_id="tx-020",
            year=2026,
            month=4,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        assert result is not None
        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc["isSplit"] is False
        assert saved_doc["splitLines"] == []
        assert saved_doc["splitCount"] == 0

    async def test_unsplit_sets_category_to_none(self, service, mock_repo, mock_audit):
        """Parent categoryId should be None after unsplit."""
        parent = make_transaction(
            id="tx-021",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
            isSplit=True,
            categoryId=None,
            splitCount=2,
            splitLines=[
                {"id": "sl-1", "amount": -100.0, "sortOrder": 1},
                {"id": "sl-2", "amount": -100.0, "sortOrder": 2},
            ],
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": False}

        await service.unsplit_transaction(
            transaction_id="tx-021",
            year=2026,
            month=4,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc["categoryId"] is None
        assert saved_doc["categorizationStatus"] == "uncategorized"

    async def test_unsplit_clears_split_category_ids(self, service, mock_repo, mock_audit):
        """splitCategoryIds should be cleared on unsplit."""
        parent = make_transaction(
            id="tx-022",
            amount=Decimal("-400.00"),
            transactionType="expense",
            isDeleted=False,
            isSplit=True,
            splitCount=2,
            splitCategoryIds=["cat-a", "cat-b"],
            splitLines=[
                {"id": "sl-1", "amount": -200.0, "sortOrder": 1},
                {"id": "sl-2", "amount": -200.0, "sortOrder": 2},
            ],
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": False}

        await service.unsplit_transaction(
            transaction_id="tx-022",
            year=2026,
            month=4,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc.get("splitCategoryIds", []) == []

    async def test_audit_logged_on_unsplit(self, service, mock_repo, mock_audit):
        """Unsplit should log an audit entry."""
        parent = make_transaction(
            id="tx-023",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
            isSplit=True,
            splitCount=2,
            splitLines=[
                {"id": "sl-1", "amount": -100.0, "sortOrder": 1},
                {"id": "sl-2", "amount": -100.0, "sortOrder": 2},
            ],
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": False}

        await service.unsplit_transaction(
            transaction_id="tx-023",
            year=2026,
            month=4,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        mock_audit.log.assert_awaited_once()
        audit_kwargs = mock_audit.log.call_args.kwargs
        assert audit_kwargs["entity_id"] == "tx-023"


# ---------------------------------------------------------------------------
# Validation — create split
# ---------------------------------------------------------------------------


class TestCreateSplitValidation:
    """Validation rules for creating a split."""

    async def test_reject_less_than_two_lines(self, service, mock_repo):
        """A split must have at least 2 lines."""
        parent = make_transaction(
            id="tx-030",
            amount=Decimal("-100.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent

        lines = _make_split_lines(amounts=[Decimal("100.00")])

        with pytest.raises(ValueError, match="[Aa]t least 2"):
            await service.split_transaction(
                transaction_id="tx-030",
                year=2026,
                month=4,
                lines=lines,
                user_id=USER_ID,
                user_name=USER_NAME,
            )

        mock_repo.replace.assert_not_awaited()

    async def test_reject_more_than_twenty_lines(self, service, mock_repo):
        """A split must have at most 20 lines."""
        parent = make_transaction(
            id="tx-031",
            amount=Decimal("-2100.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent

        # 21 lines of 100 each = 2100
        lines = _make_split_lines(amounts=[Decimal("100.00")] * 21)

        with pytest.raises(ValueError, match="[Mm]ax|[Aa]t most|20|exceed"):
            await service.split_transaction(
                transaction_id="tx-031",
                year=2026,
                month=4,
                lines=lines,
                user_id=USER_ID,
                user_name=USER_NAME,
            )

        mock_repo.replace.assert_not_awaited()

    async def test_reject_sum_mismatch(self, service, mock_repo):
        """Sum of line amounts must equal parent amount exactly."""
        parent = make_transaction(
            id="tx-032",
            amount=Decimal("-150.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent

        # Lines sum to 140, not 150
        lines = _make_split_lines(amounts=[Decimal("90.00"), Decimal("50.00")])

        with pytest.raises(ValueError, match="[Ss]um|[Bb]alance|[Mm]atch|[Ee]qual"):
            await service.split_transaction(
                transaction_id="tx-032",
                year=2026,
                month=4,
                lines=lines,
                user_id=USER_ID,
                user_name=USER_NAME,
            )

        mock_repo.replace.assert_not_awaited()

    async def test_reject_split_on_already_split_transaction(self, service, mock_repo):
        """Cannot create a split on a transaction that is already split."""
        parent = make_transaction(
            id="tx-033",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
            isSplit=True,
            splitCount=2,
            splitLines=[
                {"id": "sl-1", "amount": -100.0, "sortOrder": 1},
                {"id": "sl-2", "amount": -100.0, "sortOrder": 2},
            ],
        )
        mock_repo.get_by_id.return_value = parent

        lines = _make_split_lines(amounts=[Decimal("100.00"), Decimal("100.00")])

        with pytest.raises(ValueError, match="[Aa]lready split"):
            await service.split_transaction(
                transaction_id="tx-033",
                year=2026,
                month=4,
                lines=lines,
                user_id=USER_ID,
                user_name=USER_NAME,
            )

    async def test_reject_split_on_deleted_transaction(self, service, mock_repo):
        """Cannot split a soft-deleted transaction."""
        parent = make_transaction(
            id="tx-034",
            amount=Decimal("-100.00"),
            transactionType="expense",
            isDeleted=True,
        )
        mock_repo.get_by_id.return_value = parent

        lines = _make_split_lines(amounts=[Decimal("60.00"), Decimal("40.00")])

        with pytest.raises(ValueError, match="[Dd]eleted|[Nn]ot found"):
            await service.split_transaction(
                transaction_id="tx-034",
                year=2026,
                month=4,
                lines=lines,
                user_id=USER_ID,
                user_name=USER_NAME,
            )

    async def test_reject_split_on_nonexistent_transaction(self, service, mock_repo):
        """Cannot split a non-existent transaction."""
        mock_repo.get_by_id.return_value = None

        lines = _make_split_lines(amounts=[Decimal("50.00"), Decimal("50.00")])

        with pytest.raises(ValueError, match="[Nn]ot found"):
            await service.split_transaction(
                transaction_id="tx-nonexistent",
                year=2026,
                month=4,
                lines=lines,
                user_id=USER_ID,
                user_name=USER_NAME,
            )

    async def test_reject_line_with_invalid_category(self, service, mock_repo, mock_category_repo):
        """Reject split line referencing a non-existent category."""
        parent = make_transaction(
            id="tx-036",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_category_repo.get_by_id.return_value = None  # category not found

        lines = _make_split_lines(
            amounts=[Decimal("100.00"), Decimal("100.00")],
            category_ids=["cat-nonexistent", None],
        )

        with pytest.raises(ValueError, match="[Cc]ategory|[Ii]nvalid|[Nn]ot found"):
            await service.split_transaction(
                transaction_id="tx-036",
                year=2026,
                month=4,
                lines=lines,
                user_id=USER_ID,
                user_name=USER_NAME,
            )

    async def test_reject_line_with_subcategory_but_no_category(self, service, mock_repo, mock_category_repo):
        """A split line cannot have a subcategory without a category."""
        parent = make_transaction(
            id="tx-037",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent

        lines = _make_split_lines(
            amounts=[Decimal("100.00"), Decimal("100.00")],
            category_ids=[None, None],
            subcategory_ids=["subcat-orphan", None],
        )

        with pytest.raises(ValueError, match="[Ss]ubcategory|[Cc]ategory"):
            await service.split_transaction(
                transaction_id="tx-037",
                year=2026,
                month=4,
                lines=lines,
                user_id=USER_ID,
                user_name=USER_NAME,
            )


# ---------------------------------------------------------------------------
# Validation — update split
# ---------------------------------------------------------------------------


class TestUpdateSplitValidation:
    """Validation rules for updating a split."""

    async def test_reject_update_on_non_split_transaction(self, service, mock_repo):
        """Cannot update split lines on a transaction that is not split."""
        parent = make_transaction(
            id="tx-040",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
        )
        # Not split
        mock_repo.get_by_id.return_value = parent

        lines = _make_split_lines(amounts=[Decimal("100.00"), Decimal("100.00")])

        with pytest.raises(ValueError, match="[Nn]ot split|[Nn]ot a split"):
            await service.update_split(
                transaction_id="tx-040",
                year=2026,
                month=4,
                lines=lines,
                user_id=USER_ID,
                user_name=USER_NAME,
            )

    async def test_reject_update_sum_mismatch(self, service, mock_repo):
        """Updated split line amounts must sum to parent amount."""
        parent = make_transaction(
            id="tx-041",
            amount=Decimal("-300.00"),
            transactionType="expense",
            isDeleted=False,
            isSplit=True,
            splitCount=2,
            splitLines=[
                {"id": "sl-1", "amount": -200.0, "sortOrder": 1},
                {"id": "sl-2", "amount": -100.0, "sortOrder": 2},
            ],
        )
        mock_repo.get_by_id.return_value = parent

        # Sum = 250, not 300
        lines = _make_split_lines(amounts=[Decimal("150.00"), Decimal("100.00")])

        with pytest.raises(ValueError, match="[Ss]um|[Bb]alance|[Mm]atch|[Ee]qual"):
            await service.update_split(
                transaction_id="tx-041",
                year=2026,
                month=4,
                lines=lines,
                user_id=USER_ID,
                user_name=USER_NAME,
            )

    async def test_reject_update_less_than_two_lines(self, service, mock_repo):
        """Updated split must still have at least 2 lines."""
        parent = make_transaction(
            id="tx-042",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
            isSplit=True,
            splitCount=2,
            splitLines=[
                {"id": "sl-1", "amount": -100.0, "sortOrder": 1},
                {"id": "sl-2", "amount": -100.0, "sortOrder": 2},
            ],
        )
        mock_repo.get_by_id.return_value = parent

        lines = _make_split_lines(amounts=[Decimal("200.00")])

        with pytest.raises(ValueError, match="[Aa]t least 2"):
            await service.update_split(
                transaction_id="tx-042",
                year=2026,
                month=4,
                lines=lines,
                user_id=USER_ID,
                user_name=USER_NAME,
            )


# ---------------------------------------------------------------------------
# Validation — unsplit
# ---------------------------------------------------------------------------


class TestUnsplitValidation:
    """Validation rules for unsplitting."""

    async def test_reject_unsplit_on_non_split_transaction(self, service, mock_repo):
        """Cannot unsplit a transaction that is not split."""
        parent = make_transaction(
            id="tx-050",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent

        with pytest.raises(ValueError, match="[Nn]ot split|[Nn]ot a split"):
            await service.unsplit_transaction(
                transaction_id="tx-050",
                year=2026,
                month=4,
                user_id=USER_ID,
                user_name=USER_NAME,
            )


# ---------------------------------------------------------------------------
# Amount sign handling
# ---------------------------------------------------------------------------


class TestAmountSignHandling:
    """The service applies the parent's sign to split line amounts.

    Users provide unsigned amounts; the service stores them with the
    same sign as the parent.
    """

    async def test_expense_lines_stored_negative(self, service, mock_repo, mock_audit):
        """Expense parent: user provides 100, 50 → stored as -100, -50."""
        parent = make_transaction(
            id="tx-060",
            amount=Decimal("-150.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        lines = _make_split_lines(amounts=[Decimal("100.00"), Decimal("50.00")])

        await service.split_transaction(
            transaction_id="tx-060",
            year=2026,
            month=4,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        saved_doc = mock_repo.replace.call_args[0][1]
        stored_amounts = [Decimal(str(sl["amount"])) for sl in saved_doc["splitLines"]]
        assert stored_amounts == [Decimal("-100.00"), Decimal("-50.00")]

    async def test_income_lines_stored_positive(self, service, mock_repo, mock_audit):
        """Income parent: user provides 200, 100 → stored as 200, 100."""
        parent = make_transaction(
            id="tx-061",
            amount=Decimal("300.00"),
            transactionType="income",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        lines = _make_split_lines(amounts=[Decimal("200.00"), Decimal("100.00")])

        await service.split_transaction(
            transaction_id="tx-061",
            year=2026,
            month=3,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        saved_doc = mock_repo.replace.call_args[0][1]
        stored_amounts = [Decimal(str(sl["amount"])) for sl in saved_doc["splitLines"]]
        assert stored_amounts == [Decimal("200.00"), Decimal("100.00")]

    async def test_transfer_lines_match_parent_sign(self, service, mock_repo, mock_audit):
        """Transfer parent: negative → lines stored negative."""
        parent = make_transaction(
            id="tx-062",
            amount=Decimal("-500.00"),
            transactionType="transfer",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        lines = _make_split_lines(amounts=[Decimal("300.00"), Decimal("200.00")])

        await service.split_transaction(
            transaction_id="tx-062",
            year=2026,
            month=4,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        saved_doc = mock_repo.replace.call_args[0][1]
        stored_amounts = [Decimal(str(sl["amount"])) for sl in saved_doc["splitLines"]]
        assert stored_amounts == [Decimal("-300.00"), Decimal("-200.00")]


# ---------------------------------------------------------------------------
# Edge cases from spec §8
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases from the functional spec section 8."""

    async def test_split_transaction_with_existing_category(self, service, mock_repo, mock_audit):
        """§8.3: Splitting a categorized transaction clears parent category."""
        parent = make_transaction(
            id="tx-070",
            amount=Decimal("-500.00"),
            transactionType="expense",
            categoryId="cat-old",
            subcategoryId="subcat-old",
            categorizationStatus="manually_categorized",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        lines = _make_split_lines(amounts=[Decimal("300.00"), Decimal("200.00")])

        await service.split_transaction(
            transaction_id="tx-070",
            year=2026,
            month=4,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc["categoryId"] is None
        assert saved_doc["subcategoryId"] is None

    async def test_split_imported_transaction_preserves_batch_id(self, service, mock_repo, mock_audit):
        """§8.4: Splitting an imported transaction preserves importBatchId on parent."""
        parent = make_transaction(
            id="tx-071",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
            importBatchId="batch-001",
            importSource="bank",
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        lines = _make_split_lines(amounts=[Decimal("120.00"), Decimal("80.00")])

        await service.split_transaction(
            transaction_id="tx-071",
            year=2026,
            month=4,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        saved_doc = mock_repo.replace.call_args[0][1]
        assert saved_doc.get("importBatchId") == "batch-001"
        assert saved_doc.get("importSource") == "bank"

    async def test_decimal_precision_no_floating_point_errors(self, service, mock_repo, mock_audit):
        """AC-024-06: Decimal comparison. 33.33 + 33.33 + 33.34 = 100.00."""
        parent = make_transaction(
            id="tx-072",
            amount=Decimal("-100.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        lines = _make_split_lines(amounts=[Decimal("33.33"), Decimal("33.33"), Decimal("33.34")])

        # This should NOT raise — the amounts sum to exactly 100.00 in Decimal
        result = await service.split_transaction(
            transaction_id="tx-072",
            year=2026,
            month=4,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        assert result is not None

    async def test_decimal_precision_rejects_off_by_one_cent(self, service, mock_repo, mock_audit):
        """AC-024-06: 33.33 + 33.33 + 33.33 = 99.99 != 100.00."""
        parent = make_transaction(
            id="tx-073",
            amount=Decimal("-100.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent

        lines = _make_split_lines(amounts=[Decimal("33.33"), Decimal("33.33"), Decimal("33.33")])

        with pytest.raises(ValueError, match="[Ss]um|[Bb]alance|[Mm]atch|[Ee]qual"):
            await service.split_transaction(
                transaction_id="tx-073",
                year=2026,
                month=4,
                lines=lines,
                user_id=USER_ID,
                user_name=USER_NAME,
            )

    async def test_split_lines_get_unique_ids(self, service, mock_repo, mock_audit):
        """Each split line should receive a unique ID."""
        parent = make_transaction(
            id="tx-074",
            amount=Decimal("-200.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        lines = _make_split_lines(amounts=[Decimal("100.00"), Decimal("100.00")])

        await service.split_transaction(
            transaction_id="tx-074",
            year=2026,
            month=4,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        saved_doc = mock_repo.replace.call_args[0][1]
        ids = [sl["id"] for sl in saved_doc["splitLines"]]
        assert len(ids) == 2
        assert ids[0] != ids[1]  # unique

    async def test_split_lines_have_sort_order(self, service, mock_repo, mock_audit):
        """Split lines should have sortOrder reflecting their position."""
        parent = make_transaction(
            id="tx-075",
            amount=Decimal("-300.00"),
            transactionType="expense",
            isDeleted=False,
        )
        mock_repo.get_by_id.return_value = parent
        mock_repo.replace.return_value = {**parent, "isSplit": True}

        lines = _make_split_lines(amounts=[Decimal("100.00"), Decimal("100.00"), Decimal("100.00")])

        await service.split_transaction(
            transaction_id="tx-075",
            year=2026,
            month=4,
            lines=lines,
            user_id=USER_ID,
            user_name=USER_NAME,
        )

        saved_doc = mock_repo.replace.call_args[0][1]
        orders = [sl["sortOrder"] for sl in saved_doc["splitLines"]]
        assert orders == [1, 2, 3]
