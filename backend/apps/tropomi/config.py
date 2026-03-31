"""Configuration for TROPOMI pipeline."""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class TropomiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "methlab"
    db_user: str = "postgres"
    db_password: str = ""

    # AWS S3
    aws_region: str = "ap-southeast-2"
    s3_bucket: str = "methlab-data-apse2"

    # TROPOMI processing
    aoi_radius_km: float = 50.0  # Radius around facility centroid for AOI extraction
    min_qa_value: float = 0.5  # Minimum quality assurance value for CH4 retrievals
    background_percentile: float = 10.0  # Percentile for background CH4 estimation

    # ERA5 / CDS API
    era5_cache_dir: str = "D:/tmp/era5"
    cds_api_url: str = "https://cds.climate.copernicus.eu/api"
    cds_api_key: str = ""  # Format: UID:API_KEY

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
def get_settings() -> TropomiSettings:
    return TropomiSettings()
