from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.services.cosmos_client import cosmos_service


class CosmosCategoryRepository:
    async def list_all(self) -> list[dict]:
        query = "SELECT * FROM c ORDER BY c.sortOrder ASC"
        items = []
        async for item in cosmos_service.categories.query_items(query=query):
            items.append(item)
        return items

    async def get_by_id(self, category_id: str) -> dict | None:
        try:
            return await cosmos_service.categories.read_item(item=category_id, partition_key=category_id)
        except CosmosResourceNotFoundError:
            return None

    async def create(self, document: dict) -> dict:
        return await cosmos_service.categories.create_item(body=document)

    async def replace(self, category_id: str, document: dict) -> dict:
        return await cosmos_service.categories.replace_item(item=category_id, body=document)

    async def delete(self, category_id: str) -> None:
        await cosmos_service.categories.delete_item(item=category_id, partition_key=category_id)
