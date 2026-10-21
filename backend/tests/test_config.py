# Config tests
import pytest
from app.core.config import Settings, get_settings


def test_default_settings():
    settings = Settings()
    assert settings.app_name == "cobalt-pilot-ryan-vo"
    assert settings.app_version == "1.0.0"
    assert settings.database_url == "sqlite+aiosqlite:///./data/app.db"
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("APP_NAME", "custom-app")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./custom.db")
    monkeypatch.setenv("SECRET_KEY", "custom-secret")
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_MODEL", "claude-3-opus")
    
    settings = Settings()
    assert settings.app_name == "custom-app"
    assert settings.debug is True
    assert settings.database_url == "sqlite+aiosqlite:///./custom.db"
    assert settings.secret_key == "custom-secret"
    assert settings.llm_provider == "anthropic"
    assert settings.llm_model == "claude-3-opus"


def test_effective_oidc_issuer():
    settings = Settings(
        keycloak_url="https://auth.example.com",
        keycloak_realm="myrealm",
        oidc_issuer_url="",
    )
    assert settings.effective_oidc_issuer == "https://auth.example.com/realms/myrealm"
    
    # Explicit issuer takes precedence
    settings2 = Settings(
        keycloak_url="https://auth.example.com",
        keycloak_realm="myrealm",
        oidc_issuer_url="https://custom-issuer.example.com",
    )
    assert settings2.effective_oidc_issuer == "https://custom-issuer.example.com"


def test_cors_origins_default():
    settings = Settings()
    assert "http://localhost:5173" in settings.cors_origins
    assert "http://127.0.0.1:5173" in settings.cors_origins