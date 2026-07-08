from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    debug: bool = False
    cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    database_url: str = "DATABASE_URL"
    redis_url: str = "REDIS_URL"
    s3_access_key: str = "CHANGE_ME_S3_ACCESS_KEY"
    s3_secret_key: str = "CHANGE_ME_S3_SECRET_KEY"
    s3_endpoint_url: str = "CHANGE_ME_S3_ENDPOINT_URL"
    s3_bucket_name: str = "CHANGE_ME_S3_BUCKET_NAME"
    access_secret: str = "CHANGE_ME_ACCESS_SECRET_MIN_32_CHARS"
    refresh_secret: str = "CHANGE_ME_REFRESH_SECRET_MIN_32_CHARS"
    access_token_expire_m: int = 15  # 15 minutes
    refresh_token_expire_m: int = 43200  # 30 days
    cookie_secure: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "strict"
    engine_version: str = "1.0.0"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if value == "DATABASE_URL":
            raise ValueError("DATABASE_URL is not configured")

        if not value.startswith(("postgresql+asyncpg://", "postgres+asyncpg://")):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg")

        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        if value == "REDIS_URL":
            raise ValueError("REDIS_URL is not configured")

        if not value.startswith(("redis://", "rediss://")):
            raise ValueError("REDIS_URL must use redis:// or rediss://")

        return value

    @field_validator("access_secret", "refresh_secret")
    @classmethod
    def validate_secret_length(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT secret must be at least 32 characters long")
        return value

    model_config = SettingsConfigDict(env_file=".env", frozen=True, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
