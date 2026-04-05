import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_secret_from_file(path: str | None) -> str | None:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        return None
    return file_path.read_text(encoding="utf-8").strip()


class Settings(BaseSettings):
    app_name: str = "Timetabling Assistant API"
    api_prefix: str = "/api"
    app_env: str = "development"
    timezone_name: str = "Europe/London"
    config_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2] / ".runtime")
    database_url: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/timetabling"
    database_url_file: str | None = None
    auto_create_schema: bool = False
    expose_docs: bool = True
    request_size_limit_bytes: int = 1_048_576
    auth_token_ttl_minutes: int = 60
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 300
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"])
    jwt_secret: str | None = None
    jwt_secret_file: str | None = None
    calendar_token_secret: str | None = None
    calendar_token_secret_file: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="TIMETABLING_",
        env_file=".env",
        extra="ignore",
    )

    @computed_field
    @property
    def resolved_database_url(self) -> str:
        if self.app_env.lower() == "desktop" and self.database_url == Settings.model_fields["database_url"].default and not self.database_url_file:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{(self.config_dir / 'timetabling.db').as_posix()}"
        return _read_secret_from_file(self.database_url_file) or self.database_url

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "desktop"}

    def _ensure_secret(self, supplied: str | None, file_path: str | None, filename: str) -> str:
        if supplied:
            return supplied

        from_file = _read_secret_from_file(file_path)
        if from_file:
            return from_file

        self.config_dir.mkdir(parents=True, exist_ok=True)
        secret_path = self.config_dir / filename
        if secret_path.exists():
            return secret_path.read_text(encoding="utf-8").strip()

        generated = secrets.token_urlsafe(48)
        secret_path.write_text(generated, encoding="utf-8")
        return generated

    @property
    def resolved_jwt_secret(self) -> str:
        return self._ensure_secret(self.jwt_secret, self.jwt_secret_file, "jwt_secret")

    @property
    def resolved_calendar_token_secret(self) -> str:
        return self._ensure_secret(self.calendar_token_secret, self.calendar_token_secret_file, "calendar_secret")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.expose_docs = settings.expose_docs and not settings.is_production
    if settings.app_env.lower() == "desktop":
        settings.auto_create_schema = True
    if settings.is_production and not settings.cors_origins:
        settings.cors_origins = ["tauri://localhost"]
    return settings
