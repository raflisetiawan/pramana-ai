"""
Pramana AI — Mock VClaim Configuration.

Loads settings from environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class MockVClaimSettings(BaseSettings):
    """Mock VClaim service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service
    mock_vclaim_host: str = "0.0.0.0"
    mock_vclaim_port: int = 8001

    # Auth — Consumer credentials
    vclaim_cons_id: str = "pramana_dev_cons_id"
    vclaim_secret_key: str = "pramana_dev_secret_key_32chars_min"
    vclaim_user_key: str = "pramana_dev_user_key"

    # Simulation controls
    mock_vclaim_response_delay_ms: int = 0
    mock_vclaim_error_rate: float = 0.0

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""

    # Signature timestamp tolerance (seconds)
    signature_timestamp_tolerance: int = 300  # 5 minutes


mock_settings = MockVClaimSettings()
