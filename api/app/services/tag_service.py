from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from app.models.domain import AuditAction
from app.models.schemas import TagCreate, TagUpdate

if TYPE_CHECKING:
    from app.repositories.protocols import ReferenceItemRepository, TransactionRepository
    from app.services.audit_service import AuditService

_PARTITION_KEY = "tag"


class TagService:
    def __init__(
        self,
        *,
        repo: ReferenceItemRepository,
        audit_service: AuditService,
        transaction_repo: TransactionRepository,
    ):
        self._repo = repo
        self._audit = audit_service
        self._txn_repo = transaction_repo

    async def list_tags(self) -> list[dict]:
        return await self._repo.list_all(_PARTITION_KEY)

    async def get_tag(self, tag_id: str) -> dict | None:
        return await self._repo.get_by_id(tag_id, _PARTITION_KEY)

    async def create_tag(self, data: TagCreate, user_id: str, user_name: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        tag_id = f"tag-{uuid4().hex[:12]}"
        doc = {
            "id": tag_id,
            "type": _PARTITION_KEY,
            "name": data.name,
            "color": data.color,
            "sortOrder": data.sort_order,
            "isActive": True,
            "createdAt": now,
            "updatedAt": None,
        }

        created = await self._repo.create(doc, _PARTITION_KEY)

        await self._audit.log(
            entity_type="Tag",
            entity_id=tag_id,
            action=AuditAction.CREATE,
            changed_by=user_id,
            changed_by_name=user_name,
            new_values={"name": data.name},
        )

        return created

    async def update_tag(
        self,
        tag_id: str,
        data: TagUpdate,
        user_id: str,
        user_name: str,
    ) -> dict | None:
        existing = await self.get_tag(tag_id)
        if not existing:
            return None

        old_values = {}
        new_values = {}

        field_map = {
            "name": "name",
            "color": "color",
            "sort_order": "sortOrder",
            "is_active": "isActive",
        }

        updates = data.model_dump(exclude_unset=True)
        for py_field, doc_field in field_map.items():
            if py_field in updates:
                value = updates[py_field]
                if existing.get(doc_field) != value:
                    old_values[doc_field] = existing.get(doc_field)
                    new_values[doc_field] = value
                existing[doc_field] = value

        existing["updatedAt"] = datetime.now(timezone.utc).isoformat()

        replaced = await self._repo.replace(tag_id, existing, _PARTITION_KEY)

        if old_values:
            await self._audit.log(
                entity_type="Tag",
                entity_id=tag_id,
                action=AuditAction.UPDATE,
                changed_by=user_id,
                changed_by_name=user_name,
                old_values=old_values,
                new_values=new_values,
            )

        return replaced

    async def delete_tag(self, tag_id: str, user_id: str, user_name: str) -> bool:
        """Delete tag after verifying no transactions reference it. Raises ValueError on conflict."""
        count = await self._txn_repo.count_by_tag(tag_id)
        if count > 0:
            raise ValueError(f"Cannot delete tag: {count} transaction(s) reference it. Deactivate instead.")

        existing = await self.get_tag(tag_id)
        if not existing:
            return False

        await self._repo.delete(tag_id, _PARTITION_KEY)

        await self._audit.log(
            entity_type="Tag",
            entity_id=tag_id,
            action=AuditAction.DELETE,
            changed_by=user_id,
            changed_by_name=user_name,
        )

        return True
