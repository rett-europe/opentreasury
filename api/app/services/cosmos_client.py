from azure.cosmos.aio import CosmosClient


class CosmosService:
    _instance = None
    _client: CosmosClient | None = None
    _database = None
    _containers: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self, endpoint: str, database_name: str, key: str = ""):
        if self._client is not None:
            return
        if key:
            self._client = CosmosClient(endpoint, credential=key)
        else:
            from azure.identity.aio import DefaultAzureCredential

            credential = DefaultAzureCredential()
            self._client = CosmosClient(endpoint, credential=credential)
        self._database = self._client.get_database_client(database_name)
        self._containers = {
            "transactions": self._database.get_container_client("transactions"),
            "categories": self._database.get_container_client("categories"),
            "reference_data": self._database.get_container_client("reference_data"),
            "audit_log": self._database.get_container_client("audit_log"),
        }

    @property
    def transactions(self):
        return self._containers["transactions"]

    @property
    def categories(self):
        return self._containers["categories"]

    @property
    def reference_data(self):
        return self._containers["reference_data"]

    @property
    def audit_log(self):
        return self._containers["audit_log"]

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
            self._database = None
            self._containers = {}


cosmos_service = CosmosService()
