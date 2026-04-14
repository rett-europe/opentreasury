from app.services.cosmos_client import cosmos_service


class CosmosAuditRepository:
    async def create(self, entry: dict) -> None:
        await cosmos_service.audit_log.create_item(body=entry)

    async def query_trail(
        self,
        entity_type: str | None = None,
        entity_id: str | None = None,
        page_size: int = 20,
        continuation_token: str | None = None,
    ) -> tuple[list[dict], str | None]:
        conditions = []
        parameters = []

        if entity_type:
            conditions.append("c.entityType = @entityType")
            parameters.append({"name": "@entityType", "value": entity_type})

        if entity_id:
            conditions.append("c.entityId = @entityId")
            parameters.append({"name": "@entityId", "value": entity_id})

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM c{where} ORDER BY c.changedAt DESC"

        kwargs: dict = {
            "query": query,
            "parameters": parameters,
            "max_item_count": page_size,
        }
        if entity_type:
            kwargs["partition_key"] = entity_type

        pager = cosmos_service.audit_log.query_items(**kwargs).by_page(continuation_token)

        items = []
        async for page in pager:
            items = [item async for item in page]
            break

        return items, pager.continuation_token
