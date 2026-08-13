from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Enterprise IT Support Agent"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_it_support_agent"
    )
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_embeddings_model: str = "text-embedding-3-small"
    entra_tenant_id: str | None = None
    entra_api_client_id: str | None = None
    entra_required_scope: str = "access_as_user"
    max_history_messages: int = 24
    default_user_email: str = "employee@example.com"
    default_user_full_name: str = "Enterprise Employee"
    enable_demo_seed: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
