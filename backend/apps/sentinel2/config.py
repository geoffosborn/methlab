"""Configuration for Sentinel-2 quantification pipeline."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class S2Settings(BaseSettings):
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

    # S2 processing parameters
    max_cloud_cover: float = 30.0  # Max cloud cover percentage
    aoi_radius_km: float = 10.0  # Radius around facility for S2 scene
    min_background_scenes: int = 20  # Minimum scenes for background model
    gaussian_sigma: float = 0.7  # Gaussian filter sigma for enhancement
    upwind_sigma_threshold: float = 2.0  # Sigma threshold for upwind masking
    min_plume_pixels: int = 40  # Minimum connected pixels for a plume cluster

    # CDSE credentials (username/password for Copernicus Data Space)
    cdse_username: str = ""
    cdse_password: str = ""

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
def get_settings() -> S2Settings:
    return S2Settings()
