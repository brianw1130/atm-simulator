"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    All values are loaded from environment variables. See .env.example for defaults.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://atm_user:atm_pass@db:5432/atm_db"
    database_url_sync: str = "postgresql://atm_user:atm_pass@db:5432/atm_db"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Security
    secret_key: str = "change-me-in-production"
    pin_pepper: str = "change-me-in-production"

    # Session
    session_timeout_seconds: int = 120

    # Authentication
    max_failed_pin_attempts: int = 3
    lockout_duration_seconds: int = 1800

    # Transaction limits (in cents)
    daily_withdrawal_limit: int = 50_000  # $500.00
    daily_transfer_limit: int = 250_000  # $2,500.00

    # Statement generation
    statement_output_dir: str = "/app/statements"

    # Logging
    log_level: str = "INFO"

    # Frontend
    frontend_enabled: bool = True

    # AWS S3
    s3_bucket_name: str = ""
    aws_region: str = "us-east-1"

    # Seed data
    seed_snapshot_path: str = ""
    seed_snapshot_s3_key: str = ""

    # Environment
    environment: str = "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in test environment."""
        return self.environment == "testing"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


settings = Settings()
