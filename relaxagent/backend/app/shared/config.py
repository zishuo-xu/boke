from functools import lru_cache
import os


class Settings:
    def __init__(self) -> None:
        raw_origins = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        self.cors_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
        self.cors_origin_regex = os.getenv(
            "BACKEND_CORS_ORIGIN_REGEX",
            r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$",
        )
        self.database_url = os.getenv("BACKEND_DATABASE_URL", "sqlite:///./relaxagent.db")


@lru_cache
def get_settings() -> Settings:
    return Settings()
