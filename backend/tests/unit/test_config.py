import pytest
from backend.app.config.settings import Settings

def test_settings_initialization():
    """Verify that settings can be initialized with default values."""
    settings = Settings()
    assert settings.APP_NAME == "Loom API"
    assert settings.ENVIRONMENT in ["development", "test", "production"]

def test_validate_secrets_empty_string():
    """Verify that empty secret strings are converted to None."""
    settings = Settings(GITHUB_CLIENT_ID="")
    assert settings.GITHUB_CLIENT_ID is None

def test_validate_app_id_conversion():
    """Verify that app id can be parsed from string or int."""
    settings = Settings(GITHUB_APP_ID="12345")
    assert settings.GITHUB_APP_ID == 12345

    settings = Settings(GITHUB_APP_ID=67890)
    assert settings.GITHUB_APP_ID == 67890
