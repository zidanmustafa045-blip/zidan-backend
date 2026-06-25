"""
إعدادات التطبيق (Application Settings)
تُقرأ القيم من متغيرات البيئة أو من ملف .env الموجود في جذر المشروع.
"""

import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ----- قاعدة البيانات -----
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/agrivision"

    # ----- JWT / الأمان -----
    SECRET_KEY: str = "CHANGE-THIS-SECRET-KEY-IN-PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # يوم كامل

    # ----- خدمات خارجية -----
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"

    # ----- إعدادات عامة -----
    APP_NAME: str = "AgriVision Ultra API"
    APP_VERSION: str = "1.0.0"
    CORS_ORIGINS: list[str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        """Accept either a JSON array string or a comma-separated string,
        so misformatted env vars on any hosting provider (Render, Hugging
        Face Secrets, etc.) don't crash the app at startup."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return ["*"]
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(o).strip() for o in parsed]
            except (json.JSONDecodeError, ValueError):
                pass
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
