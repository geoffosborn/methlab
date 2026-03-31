"""Configuration settings for MethLab API."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "MethLab API"
    debug: bool = False
    port: int = 8020

    # Database (RDS PostgreSQL + PostGIS)
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "methlab"
    db_user: str = "postgres"
    db_password: str = ""

    # AWS
    aws_region: str = "ap-southeast-2"
    s3_bucket: str = "methlab-data-apse2"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    @property
    def database_url(self) -> str:
        return (
            f"host={self.db_host} "
            f"port={self.db_port} "
            f"dbname={self.db_name} "
            f"user={self.db_user} "
            f"password={self.db_password}"
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
