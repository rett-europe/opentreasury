from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.services.cosmos_client import cosmos_service

_PREFERENCES_TYPE = "user_preferences"


class CosmosUserPreferencesRepository:
    async def get(self, user_oid: str) -> dict | None:
        try:
            return await cosmos_service.reference_data.read_item(item=user_oid, partition_key=_PREFERENCES_TYPE)
        except CosmosResourceNotFoundError:
            return None

    async def upsert(self, user_oid: str, prefs: dict) -> dict:
        document = {
            "id": user_oid,
            "type": _PREFERENCES_TYPE,
            **prefs,
        }
        return await cosmos_service.reference_data.upsert_item(body=document)
