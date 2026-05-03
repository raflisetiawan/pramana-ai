"""
Pramana AI — API Gateway Configuration.

Loads settings from environment variables using pydantic-settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Environment ---
    app_env: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"

    # --- API Gateway ---
    api_gateway_host: str = "0.0.0.0"
    api_gateway_port: int = 8000
    api_gateway_workers: int = 2

    # --- JWT Auth ---
    jwt_secret_key: str = "dev_jwt_secret_key_change_in_production_min_64chars_long"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480
    jwt_refresh_token_expire_days: int = 7

    # --- PostgreSQL ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "pramana_dev"
    postgres_user: str = "pramana_user"
    postgres_password: str = "pramana_dev_password"
    database_url: str = ""
    database_url_sync: str = ""

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db_cache: int = 0
    redis_db_celery: int = 1
    redis_url: str = ""

    # --- Internal Service URLs ---
    nlp_engine_internal_url: str = "http://nlp-engine:8002"
    ml_engine_internal_url: str = "http://ml-engine:8003"
    auth_service_internal_url: str = "http://auth-service:8004"
    mock_vclaim_internal_url: str = "http://mock-vclaim:8001"

    # --- CORS ---
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    # --- Data Privacy ---
    noka_hash_iterations: int = 260000
    noka_hash_salt: str = "dev_salt_change_in_production"

    @property
    def async_database_url(self) -> str:
        """Build async database URL from components."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        """Build sync database URL for Alembic."""
        if self.database_url_sync:
            return self.database_url_sync
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",")]


settings = Settings()
