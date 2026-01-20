import hashlib
import tomllib
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, field_validator
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
    cache_version_override: str = Field(
        default="1",
        validation_alias="cache_version",
    )

    @property
    def cache_version(self) -> str:
        """
        Computes a cache version using a hash that includes:
        - The project version
        - The env-configured cache version override (allows manual cache
        invalidation)

        This ensures that the frontend cache is invalidated the fetched script
        changes.

        Note that we do not include any additional config options that are
        served to the client, since these are not cached.
        """
        values = [_get_project_version(), self.cache_version_override]
        values_str = "|".join(values)
        return hashlib.sha256(values_str.encode("utf-8")).hexdigest()

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


def _get_project_version() -> str:
    """
    Return the version of the application from the pyproject.toml file.
    """
    file_path = Path(f"{PROJECT_ROOT}/pyproject.toml")
    data = tomllib.loads(file_path.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if version is None:
        raise ValueError("Version not found in pyproject.toml")

    return str(version)
