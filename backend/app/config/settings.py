from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Loom API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "insecure-development-key"
    ALLOWED_HOSTS: List[str] = ["*"]

    # JWT Configuration
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://loom:loom@localhost:5432/loom"

    # Redis Configuration
    REDIS_URL: Optional[str] = None

    # GitHub Configuration
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_REDIRECT_URI: Optional[str] = None
    GITHUB_APP_ID: Optional[int] = None
    GITHUB_PRIVATE_KEY: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None

    GITHUB_API_URL: str = "https://api.github.com"
    GITHUB_TOKEN_URL: str = "https://github.com/login/oauth/access_token"
    GITHUB_AUTHORIZE_URL: str = "https://github.com/login/oauth/authorize"

    @field_validator("GITHUB_CLIENT_SECRET", "GITHUB_PRIVATE_KEY", "GITHUB_WEBHOOK_SECRET")
    @classmethod
    def validate_secrets(cls, v: Optional[str]) -> Optional[str]:
        if v == "":
            return None
        return v

    # AI Provider Configuration
    AI_PROVIDER: str = "loom-cloud"  # openai, anthropic, loom-cloud
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LOOM_CLOUD_API_KEY: Optional[str] = None

    # Model Settings
    DEFAULT_MODEL: str = "gpt-4o"
    AGENT_MODEL: str = "gpt-4o-mini"

    # Workspace & Cloning Settings
    WORKSPACE_BASE_DIR: str = "/tmp/loom-workspaces"
    MAX_REPO_SIZE_MB: int = 500
    CLONE_TIMEOUT_SECONDS: int = 300  # 5 minutes

    # File Discovery Settings
    MAX_FILE_SIZE_KB: int = 1024  # 1MB
    IGNORED_DIRECTORIES: List[str] = [".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"]
    IGNORED_FILES: List[str] = [".DS_Store", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"]

    # Contribution Rule Settings
    CONTRIBUTING_FILE_VARIANTS: List[str] = ["CONTRIBUTING.md", "CONTRIBUTING.rst", "CONTRIBUTING.txt", "CONTRIBUTING", "contributing.md"]
    GITHUB_DIR: str = ".github"
    ISSUE_TEMPLATE_DIRS: List[str] = ["ISSUE_TEMPLATE", "issue_template"]
    PULL_REQUEST_TEMPLATE_VARIANTS: List[str] = ["PULL_REQUEST_TEMPLATE.md", "pull_request_template.md"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
