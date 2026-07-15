from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173"
)


class Settings(BaseSettings):
    cors_origins: str = DEFAULT_CORS_ORIGINS
    localhub_db_path: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    def resolve_database_path(self, default_path: Path) -> Path:
        if not self.localhub_db_path:
            return default_path

        return Path(self.localhub_db_path).expanduser().resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
