from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql+psycopg://tributaria:tributaria@localhost:5432/tributaria"
    admin_api_enabled: bool = True
    segregation_of_duties_enabled: bool = True
    session_ttl_seconds: int = 28800
    session_cookie_name: str = "tributaria_session"
    csrf_cookie_name: str = "tributaria_csrf"
    normative_artifact_root: str = "database/normative-artifacts/ingested"
    tax_rule_specification_root: str = "docs/tax/rules/specifications"
    batch_max_rows: int = 500
    batch_max_file_size_bytes: int = 5_000_000

    @property
    def is_production(self) -> bool:
        return self.app_env.casefold() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
