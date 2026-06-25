"""
إعدادات التطبيق (Application Settings)
تُقرأ القيم من متغيرات البيئة أو من ملف .env الموجود في جذر المشروع.
"""

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
