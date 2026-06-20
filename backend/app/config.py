from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env.local", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql://fieldintel:fieldintel@localhost:5433/fieldintel"
    )
    storage_backend: str = "local"
    upload_dir: str = "./uploads"
    gemini_api_key: str = ""
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:5173"
    max_upload_size_mb: int = 10

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        if path.is_absolute():
            return path
        # backend/app/config.py -> project root is two levels up
        project_root = Path(__file__).resolve().parents[2]
        return (project_root / path).resolve()


settings = Settings()
