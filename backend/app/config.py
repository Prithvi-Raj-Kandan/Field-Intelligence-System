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

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
