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
    s3_bucket: str = ""
    aws_region: str = "ap-south-1"
    # Optional — omit on App Runner (uses instance role). Set locally to test S3 without IAM role.
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    # Transcription: note images + voice memos (separate quota)
    gemini_transcribe_api_key: str = ""
    gemini_transcribe_model: str = "gemini-2.5-flash"
    # Debrief generation (separate quota)
    gemini_debrief_api_key: str = ""
    gemini_debrief_model: str = "gemini-2.5-flash"
    # Legacy fallback if split keys not set
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 480
    cors_origins: str = "http://localhost:5173"
    max_upload_size_mb: int = 10
    environment: str = "development"
    cookie_secure: bool = False
    allow_manager_registration: bool = False
    auth_cookie_name: str = "access_token"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        if path.is_absolute():
            return path
        project_root = Path(__file__).resolve().parents[2]
        return (project_root / path).resolve()

    def resolved_transcribe_api_key(self) -> str:
        return self.gemini_transcribe_api_key or self.gemini_api_key

    def resolved_debrief_api_key(self) -> str:
        return self.gemini_debrief_api_key or self.gemini_api_key


settings = Settings()
