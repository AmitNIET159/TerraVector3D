"""Application configuration via environment variables."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "postgresql://bhudrishti:bhudrishti@localhost:5432/bhudrishti3d"
    DATABASE_ECHO: bool = False
    DEBUG: bool = False
    APP_VERSION: str = "0.1.0"
    APP_TITLE: str = "BhuDrishti 3D"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
