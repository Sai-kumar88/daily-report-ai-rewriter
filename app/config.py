from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    APP_NAME: str = Field(default="Daily Report AI", description="Name of the application")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    APP_ENV: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=False, description="Debug mode flag")
    HOST: str = Field(default="0.0.0.0", description="Server bind host")
    PORT: int = Field(default=8080, description="Server bind port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # CORS settings
    CORS_ORIGINS: List[str] = Field(default=["*"], description="Allowed CORS origins")

    # NVIDIA NIM API Settings
    NVIDIA_API_KEY: str = Field(
        default="",
        description="NVIDIA NIM API key for authenticating requests.",
    )
    NVIDIA_BASE_URL: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="NVIDIA NIM API base URL.",
    )
    NVIDIA_MODEL: str = Field(
        default="nvidia/nemotron-3.5-lightning-30b-a3b",
        description="NVIDIA AI model to use for rewriting daily reports.",
    )
    REQUEST_TIMEOUT_SECONDS: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds for NVIDIA API calls.",
    )
    MAX_RETRIES: int = Field(
        default=2,
        description="Maximum retry attempts for transient upstream failures.",
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid_levels:
            return "INFO"
        return upper


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached singleton instance of application settings."""
    return Settings()

