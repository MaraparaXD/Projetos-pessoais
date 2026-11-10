from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore", hide_input_in_errors=True)
    environment: str = "development"
    database_url: str = Field(default="sqlite:///./sentinel.db", repr=False)
    redis_url: str = Field(default="", repr=False)
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    bootstrap_admin_email: str = ""
    bootstrap_admin_password: str = Field(default="", repr=False)
    bootstrap_webhook_secret: str = Field(default="", repr=False)
    integration_encryption_key: str = Field(default="", repr=False)
    session_hours: int = 8
    max_body_bytes: int = 65536
    reopen_window_seconds: int = 900
    flapping_window_seconds: int = 600
    flapping_threshold: int = 4
    webhook_clock_skew_seconds: int = 300
    event_retention_days: int = 90
    audit_retention_days: int = 365
    rate_limit_per_minute: int = 300
    login_rate_limit_per_minute: int = 10

    @model_validator(mode="after")
    def production_requirements(self):
        if self.environment not in {"development", "test", "production"}:
            raise ValueError("Invalid environment")
        if self.environment == "production":
            if not self.integration_encryption_key:
                raise ValueError("Production requires INTEGRATION_ENCRYPTION_KEY")
            if not self.database_url.startswith("postgresql") or not self.redis_url:
                raise ValueError("Production requires PostgreSQL and Redis")
            if self.bootstrap_admin_password or self.bootstrap_webhook_secret:
                raise ValueError("Disable bootstrap credentials in production; provision with CLI")
            if not self.cors_origins or any(not o.startswith("https://") for o in self.cors_origins):
                raise ValueError("Production requires explicit HTTPS origins")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
