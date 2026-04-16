from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AZURE_TENANT_ID: str
    ENTRA_API_CLIENT_ID: str
    COSMOS_ENDPOINT: str
    COSMOS_DATABASE_NAME: str = "opentreasury"
    COSMOS_KEY: str = ""  # Leave empty for Entra ID RBAC auth (production + local dev via az login)
    CORS_ORIGINS: str = "http://localhost:4200"  # Comma-separated or JSON array

    model_config = {"env_file": ".env", "case_sensitive": True}

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS as comma-separated string or JSON array."""
        import json

        val = self.CORS_ORIGINS.strip()
        if val.startswith("["):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                pass
        return [origin.strip() for origin in val.split(",") if origin.strip()]


settings = Settings()
