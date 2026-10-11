import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Lab3: pick the env file by APP_ENV (config/.env.sandbox, config/.env.production),
# layered on top of a shared config/.env so sandbox and production stay isolated.
_APP_ENV = os.getenv("APP_ENV", "development")
_ENV_FILES = ("config/.env", f"config/.env.{_APP_ENV}")


class Settings(BaseSettings):
    """Application settings, populated from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=_ENV_FILES, extra="ignore")

    app_env: str = _APP_ENV
    debug: bool = True
    log_level: str = "INFO"
    # Lab3: opt-in route that raises on purpose, to show the 500 handler
    # (detailed body in dev, generic in production). Off unless explicitly enabled.
    enable_demo_error_route: bool = False
    database_url: str = "postgresql+asyncpg://cyberimplant:cyberimplant@localhost:5433/cyberimplant"

    # Lab2: JWT auth.
    secret_key: str = "dev-insecure-secret-change-me-in-production-0123456789"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
