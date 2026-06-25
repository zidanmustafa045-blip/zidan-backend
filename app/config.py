"""
إعدادات التطبيق (Application Settings)
تُقرأ القيم من متغيرات البيئة أو من ملف .env الموجود في جذر المشروع.
"""

import json

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
    # يُخزَّن كنص خام (str) عمداً، وليس list[str]، لأن pydantic-settings يحاول
    # فك تشفير JSON تلقائياً لأي حقل من نوع list قبل أن تصل القيمة لأي
    # validator خاص بنا - فإذا كانت القيمة في .env / Secrets غير JSON صالح
    # تماماً (مثلاً بسبب اختلاف طريقة الإدخال بين Render و Hugging Face
    # و Railway) يتعطل تشغيل التطبيق بالكامل عند الإقلاع. لذلك نقرأها كنص
    # ثم نحوّلها بأنفسنا عبر الخاصية cors_origins أدناه.
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins(self) -> list[str]:
        v = self.CORS_ORIGINS.strip()
        if not v or v == "*":
            return ["*"]
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return [str(o).strip() for o in parsed]
        except (json.JSONDecodeError, ValueError):
            pass
        return [o.strip() for o in v.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
