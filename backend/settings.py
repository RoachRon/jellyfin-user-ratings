from pathlib import Path
from typing import Annotated, Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])


class Settings(BaseSettings):
    """
    Runtime configuration loaded from environment variables.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_path: str = f"{PROJECT_ROOT}/data/recommendations.db"
    app_root_path: str = "/updoot"
    jellyfin_url: str
    jellyfin_api_key: str
    # Accept comma-separated values from env without requiring JSON syntax.
    # (By default, pydantic-settings tries to JSON-decode list fields.)
    admin_user_ids: Annotated[list[str], NoDecode] = []
    log_level: str = "INFO"
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


settings = Settings()  # type: ignore[call-arg]
