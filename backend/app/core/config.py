from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/gogig_vehicle_pipeline"
    upload_dir: Path = Path("uploads")
    allowed_mime_types: str = "image/jpeg,image/png,image/webp"
    cors_origins: str = "http://localhost:5173"
    blur_threshold: float = 100.0
    low_light_threshold: float = 60.0
    duplicate_hash_distance: int = 6
    min_image_width: int = 640
    min_image_height: int = 480
    ocr_enabled: bool = True
    log_level: str = "INFO"
    @property
    def allowed_mimes(self) -> set[str]: return {x.strip() for x in self.allowed_mime_types.split(",") if x.strip()}
    @property
    def cors_origin_list(self) -> list[str]: return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

@lru_cache
def get_settings() -> Settings: return Settings()
