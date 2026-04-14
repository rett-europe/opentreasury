from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.account_service import AccountService
    from app.services.category_service import CategoryService
    from app.services.tag_service import TagService


class ReferenceDataService:
    def __init__(
        self,
        *,
        account_service: AccountService,
        category_service: CategoryService,
        tag_service: TagService,
    ):
        self._accounts = account_service
        self._categories = category_service
        self._tags = tag_service

    async def get_all(self) -> dict:
        """Load all reference data in one call for frontend caching."""
        accounts = await self._accounts.list_accounts()
        categories = await self._categories.list_categories()
        tags = await self._tags.list_tags()
        return {
            "accounts": accounts,
            "categories": categories,
            "tags": tags,
        }
