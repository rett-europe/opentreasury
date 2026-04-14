from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from app.models.domain import AuditAction
from app.models.schemas import (
    CategoryCreate,
    CategoryUpdate,
    SubcategoryCreate,
    SubcategoryUpdate,
)

if TYPE_CHECKING:
    from app.repositories.protocols import CategoryRepository, TransactionRepository
    from app.services.audit_service import AuditService


class CategoryService:
    def __init__(
        self,
        *,
        repo: CategoryRepository,
        audit_service: AuditService,
        transaction_repo: TransactionRepository,
    ):
        self._repo = repo
        self._audit = audit_service
        self._txn_repo = transaction_repo

    async def list_categories(self) -> list[dict]:
        return await self._repo.list_all()

    async def get_category(self, category_id: str) -> dict | None:
        return await self._repo.get_by_id(category_id)

    async def create_category(self, data: CategoryCreate, user_id: str, user_name: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        cat_id = str(uuid4())
        doc = {
            "id": cat_id,
            "type": "category",
            "name": data.name,
            "description": data.description,
            "categoryType": data.category_type.value,
            "sortOrder": data.sort_order,
            "isActive": True,
            "subcategories": [
                {
                    "id": str(uuid4()),
                    "name": sub.name,
                    "isActive": True,
                }
                for sub in data.subcategories
            ],
            "createdAt": now,
            "updatedAt": None,
        }

        created = await self._repo.create(doc)

        await self._audit.log(
            entity_type="Category",
            entity_id=cat_id,
            action=AuditAction.CREATE,
            changed_by=user_id,
            changed_by_name=user_name,
            new_values={"name": data.name},
        )

        return created

    async def update_category(
        self,
        category_id: str,
        data: CategoryUpdate,
        user_id: str,
        user_name: str,
    ) -> dict | None:
        existing = await self.get_category(category_id)
        if not existing:
            return None

        old_values = {}
        new_values = {}

        if data.name is not None and existing.get("name") != data.name:
            old_values["name"] = existing.get("name")
            new_values["name"] = data.name
            existing["name"] = data.name

        if data.category_type is not None and existing.get("categoryType") != data.category_type.value:
            old_values["categoryType"] = existing.get("categoryType")
            new_values["categoryType"] = data.category_type.value
            existing["categoryType"] = data.category_type.value

        if data.description is not None:
            existing["description"] = data.description

        if data.sort_order is not None:
            existing["sortOrder"] = data.sort_order

        if data.is_active is not None:
            old_values["isActive"] = existing.get("isActive")
            new_values["isActive"] = data.is_active
            existing["isActive"] = data.is_active

        if data.subcategories is not None:
            # Rebuild subcategories list: match by ID first, then by name, assign new IDs for new ones
            old_subs_by_id = {s.get("id"): s for s in existing.get("subcategories", [])}
            new_subs = []
            for sub in data.subcategories:
                if sub.id and sub.id in old_subs_by_id:
                    # Existing subcategory — preserve ID and isActive, update name
                    existing_sub = old_subs_by_id[sub.id]
                    existing_sub["name"] = sub.name
                    new_subs.append(existing_sub)
                else:
                    new_subs.append(
                        {
                            "id": sub.id or str(uuid4()),
                            "name": sub.name,
                            "isActive": True,
                        }
                    )
            existing["subcategories"] = new_subs

        existing["updatedAt"] = datetime.now(timezone.utc).isoformat()

        replaced = await self._repo.replace(category_id, existing)

        if old_values:
            await self._audit.log(
                entity_type="Category",
                entity_id=category_id,
                action=AuditAction.UPDATE,
                changed_by=user_id,
                changed_by_name=user_name,
                old_values=old_values,
                new_values=new_values,
            )

        return replaced

    async def delete_category(self, category_id: str, user_id: str, user_name: str) -> bool:
        """Delete category after verifying no transactions reference it. Raises ValueError on conflict."""
        count = await self._txn_repo.count_by_category(category_id)
        if count > 0:
            raise ValueError(f"Cannot delete category: {count} transaction(s) reference it. Deactivate instead.")

        existing = await self.get_category(category_id)
        if not existing:
            return False

        await self._repo.delete(category_id)

        await self._audit.log(
            entity_type="Category",
            entity_id=category_id,
            action=AuditAction.DELETE,
            changed_by=user_id,
            changed_by_name=user_name,
        )

        return True

    async def add_subcategory(
        self,
        category_id: str,
        data: SubcategoryCreate,
        user_id: str,
        user_name: str,
    ) -> dict | None:
        existing = await self.get_category(category_id)
        if not existing:
            return None

        new_sub = {
            "id": str(uuid4()),
            "name": data.name,
            "isActive": True,
        }
        existing.setdefault("subcategories", []).append(new_sub)
        existing["updatedAt"] = datetime.now(timezone.utc).isoformat()

        replaced = await self._repo.replace(category_id, existing)

        await self._audit.log(
            entity_type="Category",
            entity_id=category_id,
            action=AuditAction.UPDATE,
            changed_by=user_id,
            changed_by_name=user_name,
            new_values={"addedSubcategory": new_sub},
        )

        return replaced

    async def update_subcategory(
        self,
        category_id: str,
        subcategory_id: str,
        data: SubcategoryUpdate,
        user_id: str,
        user_name: str,
    ) -> dict | None:
        existing = await self.get_category(category_id)
        if not existing:
            return None

        found = False
        for sub in existing.get("subcategories", []):
            if sub.get("id") == subcategory_id:
                if data.name is not None:
                    sub["name"] = data.name
                if data.is_active is not None:
                    sub["isActive"] = data.is_active
                found = True
                break

        if not found:
            return None

        existing["updatedAt"] = datetime.now(timezone.utc).isoformat()

        replaced = await self._repo.replace(category_id, existing)

        await self._audit.log(
            entity_type="Category",
            entity_id=category_id,
            action=AuditAction.UPDATE,
            changed_by=user_id,
            changed_by_name=user_name,
            new_values={"updatedSubcategory": subcategory_id},
        )

        return replaced

    async def remove_subcategory(
        self,
        category_id: str,
        subcategory_id: str,
        user_id: str,
        user_name: str,
    ) -> dict | None:
        existing = await self.get_category(category_id)
        if not existing:
            return None

        subcategories = existing.get("subcategories", [])
        original_len = len(subcategories)
        existing["subcategories"] = [s for s in subcategories if s.get("id") != subcategory_id]

        if len(existing["subcategories"]) == original_len:
            return None

        existing["updatedAt"] = datetime.now(timezone.utc).isoformat()

        replaced = await self._repo.replace(category_id, existing)

        await self._audit.log(
            entity_type="Category",
            entity_id=category_id,
            action=AuditAction.UPDATE,
            changed_by=user_id,
            changed_by_name=user_name,
            old_values={"removedSubcategoryId": subcategory_id},
        )

        return replaced
