"""Phase B parity tests — SqliteCategoryRepository + SqliteReferenceItemRepository.

Mirrors the Cosmos document shape that the existing service layer
consumes. See ``tests/test_sqlite_audit_userprefs_parity.py`` for the
overall parity-gate rationale.
"""

from __future__ import annotations

from uuid import uuid4

import pytest


# ---------------------------------------------------------------------------
# Category factories
# ---------------------------------------------------------------------------


def _category_doc(**overrides) -> dict:
    cat_id = overrides.pop("id", f"cat-{uuid4().hex[:8]}")
    base = {
        "id": cat_id,
        "type": "category",
        "name": "Donations",
        "description": "Income from donors",
        "categoryType": "income",
        "sortOrder": 1,
        "subcategories": [
            {"id": "sub-1", "name": "Individual", "isActive": True},
            {"id": "sub-2", "name": "Corporate", "isActive": True},
        ],
        "createdBy": "user-1",
        "createdAt": "2026-04-01T10:00:00+00:00",
        "updatedAt": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# CategoryRepository
# ---------------------------------------------------------------------------


class TestSqliteCategoryRepositoryParity:
    @pytest.fixture
    def repo(self, sqlite_engine_factory):
        from app.repositories.sqlite.category_repo import SqliteCategoryRepository

        return SqliteCategoryRepository(engine_factory=sqlite_engine_factory)

    async def test_create_then_get_round_trips_document(self, repo):
        doc = _category_doc()
        created = await repo.create(doc)

        for camel_key in ("id", "name", "categoryType", "sortOrder", "subcategories", "createdAt", "isDeleted"):
            assert camel_key in created
        assert created["categoryType"] == "income"
        assert created["isDeleted"] is False
        assert len(created["subcategories"]) == 2
        assert created["subcategories"][0]["id"] == "sub-1"

        fetched = await repo.get_by_id(doc["id"])
        assert fetched is not None
        assert fetched["id"] == doc["id"]
        assert fetched["subcategories"] == doc["subcategories"]

    async def test_get_unknown_returns_none(self, repo):
        assert await repo.get_by_id("nope") is None

    async def test_list_all_returns_only_non_deleted_in_sort_order(self, repo):
        await repo.create(_category_doc(id="cat-c", name="Charlie", sortOrder=3))
        await repo.create(_category_doc(id="cat-a", name="Alpha", sortOrder=1))
        await repo.create(_category_doc(id="cat-b", name="Bravo", sortOrder=2))
        deleted = _category_doc(id="cat-x", name="Deleted", sortOrder=0, isDeleted=True)
        await repo.create(deleted)

        items = await repo.list_all()
        ids = [c["id"] for c in items]
        assert ids == ["cat-a", "cat-b", "cat-c"]
        # Soft-deleted hidden by default.
        assert "cat-x" not in ids

    async def test_replace_overwrites_fields_and_persists(self, repo):
        doc = _category_doc(id="cat-r", name="Original")
        await repo.create(doc)

        updated = {
            **doc,
            "name": "Renamed",
            "categoryType": "expense",
            "subcategories": [{"id": "sub-z", "name": "Solo"}],
        }
        replaced = await repo.replace("cat-r", updated)
        assert replaced["name"] == "Renamed"
        assert replaced["categoryType"] == "expense"
        assert replaced["subcategories"][0]["id"] == "sub-z"

        fetched = await repo.get_by_id("cat-r")
        assert fetched["name"] == "Renamed"

    async def test_replace_bumps_version(self, repo):
        doc = _category_doc(id="cat-v")
        created = await repo.create(doc)
        first_version = created["version"]

        await repo.replace("cat-v", {**doc, "name": "v2"})
        await repo.replace("cat-v", {**doc, "name": "v3"})
        fetched = await repo.get_by_id("cat-v")
        assert fetched["version"] == first_version + 2

    async def test_delete_hard_removes_row(self, repo):
        doc = _category_doc(id="cat-d")
        await repo.create(doc)
        await repo.delete("cat-d")
        assert await repo.get_by_id("cat-d") is None


# ---------------------------------------------------------------------------
# Reference items factories
# ---------------------------------------------------------------------------


def _account_doc(**overrides) -> dict:
    base = {
        "id": f"acc-{uuid4().hex[:8]}",
        "type": "account",
        "name": "Main Account",
        "description": None,
        "sortOrder": 1,
        "currency": "EUR",  # type-specific attribute, hoisted to top-level
        "iban": "ES00 0000 0000 0000 0000 0000",
        "createdBy": "user-1",
        "createdAt": "2026-04-01T10:00:00+00:00",
    }
    base.update(overrides)
    return base


def _tag_doc(**overrides) -> dict:
    base = {
        "id": f"tag-{uuid4().hex[:8]}",
        "type": "tag",
        "name": "Urgent",
        "description": None,
        "sortOrder": 1,
        "color": "#ff0000",  # type-specific
        "createdBy": "user-1",
        "createdAt": "2026-04-01T10:00:00+00:00",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# ReferenceItemRepository
# ---------------------------------------------------------------------------


class TestSqliteReferenceItemRepositoryParity:
    @pytest.fixture
    def repo(self, sqlite_engine_factory):
        from app.repositories.sqlite.reference_item_repo import SqliteReferenceItemRepository

        return SqliteReferenceItemRepository(engine_factory=sqlite_engine_factory)

    async def test_create_account_then_get(self, repo):
        doc = _account_doc(id="acc-1")
        created = await repo.create(doc, "account")

        # Type-specific attrs hoisted to top-level (Cosmos parity).
        assert created["currency"] == "EUR"
        assert created["iban"].startswith("ES00")
        assert created["type"] == "account"

        fetched = await repo.get_by_id("acc-1", "account")
        assert fetched is not None
        assert fetched["currency"] == "EUR"

    async def test_get_with_wrong_type_returns_none(self, repo):
        await repo.create(_account_doc(id="acc-x"), "account")
        assert await repo.get_by_id("acc-x", "tag") is None

    async def test_list_all_filters_by_type(self, repo):
        await repo.create(_account_doc(id="acc-1", name="Alpha"), "account")
        await repo.create(_account_doc(id="acc-2", name="Bravo"), "account")
        await repo.create(_tag_doc(id="tag-1", name="Red"), "tag")

        accounts = await repo.list_all("account")
        tags = await repo.list_all("tag")
        assert {a["id"] for a in accounts} == {"acc-1", "acc-2"}
        assert {t["id"] for t in tags} == {"tag-1"}

    async def test_list_all_ordered_by_sort_then_name(self, repo):
        await repo.create(_account_doc(id="acc-c", name="Charlie", sortOrder=2), "account")
        await repo.create(_account_doc(id="acc-a", name="Alpha", sortOrder=1), "account")
        await repo.create(_account_doc(id="acc-b", name="Bravo", sortOrder=1), "account")

        ids = [a["id"] for a in await repo.list_all("account")]
        # sortOrder ASC then name ASC: alpha(1) < bravo(1) < charlie(2)
        assert ids == ["acc-a", "acc-b", "acc-c"]

    async def test_replace_updates_type_specific_attributes(self, repo):
        doc = _tag_doc(id="tag-r", name="Old", color="#000000")
        await repo.create(doc, "tag")
        updated = {**doc, "name": "New", "color": "#ffffff"}
        out = await repo.replace("tag-r", updated, "tag")
        assert out["name"] == "New"
        assert out["color"] == "#ffffff"

    async def test_delete_hard_removes(self, repo):
        await repo.create(_account_doc(id="acc-del"), "account")
        await repo.delete("acc-del", "account")
        assert await repo.get_by_id("acc-del", "account") is None

    async def test_soft_deleted_excluded_from_list(self, repo):
        await repo.create(_account_doc(id="acc-keep"), "account")
        await repo.create(_account_doc(id="acc-gone", isDeleted=True), "account")
        ids = {a["id"] for a in await repo.list_all("account")}
        assert ids == {"acc-keep"}
