from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Loom API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "insecure-development-key"
    ALLOWED_HOSTS: List[str] = ["*"]

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://loom:loom@localhost:5432/loom"

    # Redis Configuration
    REDIS_URL: Optional[str] = None

    # GitHub Configuration
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_APP_ID: Optional[int] = None
    GITHUB_PRIVATE_KEY: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None

    # AI Provider Configuration
    AI_PROVIDER: str = "loom-cloud"  # openai, anthropic, loom-cloud
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LOOM_CLOUD_API_KEY: Optional[str] = None

    # Model Settings
    DEFAULT_MODEL: str = "gpt-4o"
    AGENT_MODEL: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
