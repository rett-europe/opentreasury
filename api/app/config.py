from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AZURE_TENANT_ID: str
    ENTRA_API_CLIENT_ID: str
    COSMOS_ENDPOINT: str
    COSMOS_DATABASE_NAME: str = "opentreasury"
    COSMOS_KEY: str = ""  # Optional: set for local dev. In Azure, Managed Identity is used instead.
    CORS_ORIGINS: str = "http://localhost:4200"  # Comma-separated or JSON array

    # ------------------------------------------------------------------
    # Repository backend selector (Phase A — Electron + SQLite spec §4.2).
    # `cosmos` keeps existing cloud behavior. `sqlite` activates the desktop
    # repository implementations (skeletons in Phase A; complete in Phase B).
    # Default MUST remain `cosmos` so existing deployments are unaffected.
    # ------------------------------------------------------------------
    DATA_BACKEND: Literal["cosmos", "sqlite"] = "cosmos"

    # SQLite-specific settings (only consulted when DATA_BACKEND=sqlite).
    # Path may be a local filesystem path (Local mode) or a OneDrive-synced
    # path (Team mode). The application does not infer mode from the path —
    # mode is set explicitly per spec §6.3.
    SQLITE_DB_PATH: str = "opentreasury.db"

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
