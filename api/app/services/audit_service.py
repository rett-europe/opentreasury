from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from app.models.domain import AuditAction

if TYPE_CHECKING:
    from app.repositories.protocols import AuditRepository

_AUDIT_TTL = 220752000  # 7 years in seconds


class AuditService:
    def __init__(self, *, repo: AuditRepository):
        self._repo = repo

    async def log(
        self,
        entity_type: str,
        entity_id: str,
        action: AuditAction,
        changed_by: str,
        changed_by_name: str = "",
        old_values: dict | None = None,
        new_values: dict | None = None,
    ):
        entry = {
            "id": str(uuid4()),
            "entityType": entity_type,
            "entityId": entity_id,
            "action": action.value,
            "changedBy": changed_by,
            "changedByName": changed_by_name,
            "changedAt": datetime.now(timezone.utc).isoformat(),
            "oldValues": old_values or {},
            "newValues": new_values or {},
            "ttl": _AUDIT_TTL,
        }
        await self._repo.create(entry)

    async def query_trail(
        self,
        entity_type: str | None = None,
        entity_id: str | None = None,
        page_size: int = 20,
        continuation_token: str | None = None,
    ) -> tuple[list[dict], str | None]:
        return await self._repo.query_trail(
            entity_type=entity_type,
            entity_id=entity_id,
            page_size=page_size,
            continuation_token=continuation_token,
        )
