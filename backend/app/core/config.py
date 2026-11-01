"""FamCore Application Configuration.

Loads configuration from environment variables and .env files using Pydantic Settings.
Centralizes all application settings, database URLs, and security keys.
"""

from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core Application
    app_name: str = "FamCore"
    app_env: str = "development"
    debug: bool = True
    port: int = 8000
    api_v1_prefix: str = "/api/v1"

    # CORS Configuration
    allowed_origins: Union[List[str], str] = ["http://localhost:3000"]

    # Security & JWT
    secret_key: str = "dev_secret_key_change_in_production_min_32_characters_random"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Database & Storage
    # Default: local async SQLite for zero-friction local development without Docker
    database_url: str = "sqlite+aiosqlite:///./famcore_dev.db"
    redis_url: str | None = None

    # Object Storage
    storage_provider: str = "local"  # "local" | "s3"
    storage_local_dir: str = "./storage/uploads"
    s3_endpoint_url: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket_name: str = "famcore-vault"
    s3_region: str = "ap-south-1"

    # AI & Speech Provider Configurations
    provider_mode: str = "mock"  # "mock" | "production"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "text-embedding-004"

    gnani_api_key: str | None = None
    gnani_prisma_url: str = "https://api.gnani.ai/v1/stt"
    gnani_timbre_url: str = "https://api.gnani.ai/v1/tts"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("production", "prod")


settings = Settings()
