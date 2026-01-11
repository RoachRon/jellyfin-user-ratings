from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

from pydantic import field_validator


class Settings(BaseSettings):
    """
    Runtime configuration loaded from environment variables.

    Note: we keep the env var names stable (UPDOOT_* plus VERSION) using `validation_alias`.
    """

    model_config = SettingsConfigDict(extra="ignore")

    # --- Backend ---
    db_path: str = "/data/recommendations.db"
    jellyfin_url: str
    jellyfin_api_key: str
    admin_user_ids: list[str] = []
    log_level: str = "INFO"

    # --- JS generation ---
    backend_path: str = "/updoot"
    backend_url: str | None = None
    server_url_fallback: str | None = None
    updoot_src: str = "/updoot/assets/updoot.js"
    cache_version: str = "1"

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def _parse_admin_user_ids(cls, v: Any) -> list[str]:
        user_ids = []
        if isinstance(v, list):
            user_ids = v
        elif isinstance(v, str):
            user_ids = v.split(",")
        elif v is not None:
            user_ids = [v]

        return [val.strip() for val in user_ids if val.strip()]

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, v: Any) -> str | None:
        if v is None:
            return None
        return str(v).strip().upper()

    @field_validator("jellyfin_url", mode="before")
    @classmethod
    def _normalize_jellyfin_url(cls, v: Any) -> str | None:
        if v is None:
            return None
        return str(v).strip().rstrip("/")

