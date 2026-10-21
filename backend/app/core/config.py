# Core configuration
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # App
    app_name: str = "cobalt-pilot-ryan-vo"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # Security
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Keycloak / OIDC
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "cobalt"
    keycloak_client_id: str = "cobalt-pilot"
    keycloak_client_secret: str = ""
    oidc_issuer_url: str = ""
    oidc_audience: str = "cobalt-pilot"

    # LLM
    llm_api_key: Optional[str] = None
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: Optional[str] = None
    llm_timeout_seconds: int = 30

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Reference repo
    reference_repo_url: str = "https://github.com/anthropics/knowledge-work-plugins"
    reference_repo_branch: str = "main"

    @property
    def effective_oidc_issuer(self) -> str:
        return self.oidc_issuer_url or f"{self.keycloak_url}/realms/{self.keycloak_realm}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()