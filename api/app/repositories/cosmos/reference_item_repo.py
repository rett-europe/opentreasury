from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.services.cosmos_client import cosmos_service


class CosmosReferenceItemRepository:
    async def list_all(self, item_type: str) -> list[dict]:
        query = "SELECT * FROM c WHERE c.type = @type ORDER BY c.sortOrder ASC"
        parameters = [{"name": "@type", "value": item_type}]
        items = []
        async for item in cosmos_service.reference_data.query_items(
            query=query,
            parameters=parameters,
            partition_key=item_type,
        ):
            items.append(item)
        return items

    async def get_by_id(self, item_id: str, item_type: str) -> dict | None:
        try:
            item = await cosmos_service.reference_data.read_item(item=item_id, partition_key=item_type)
            if item.get("type") != item_type:
                return None
            return item
        except CosmosResourceNotFoundError:
            return None

    async def create(self, document: dict, item_type: str) -> dict:
        return await cosmos_service.reference_data.create_item(body=document)

    async def replace(self, item_id: str, document: dict, item_type: str) -> dict:
        return await cosmos_service.reference_data.replace_item(item=item_id, body=document)

    async def delete(self, item_id: str, item_type: str) -> None:
        await cosmos_service.reference_data.delete_item(item=item_id, partition_key=item_type)
