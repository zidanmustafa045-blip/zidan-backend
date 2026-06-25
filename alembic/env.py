"""
بيئة تشغيل Alembic — تربط ملف الترحيل بإعدادات التطبيق ونماذج SQLAlchemy
لدعم الإنشاء التلقائي للترحيلات (autogenerate) بمقارنة النماذج بقاعدة البيانات الفعلية.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# إضافة جذر المشروع لمسار البحث عن الموديولات (لاستيراد app.*)
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402
from app import models  # noqa: E402  # يضمن تحميل كل الجداول قبل autogenerate

# كائن إعدادات Alembic، يقرأ من alembic.ini
config = context.config

# تمرير رابط قاعدة البيانات من إعدادات التطبيق (متغيرات البيئة / .env)
# بدلاً من القيمة الثابتة الموجودة في alembic.ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# البيانات الوصفية (metadata) المستخدمة في المقارنة التلقائية للترحيلات
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """تشغيل الترحيلات في نمط 'offline' (يولّد SQL فقط بدون اتصال فعلي)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """تشغيل الترحيلات في نمط 'online' (يتصل فعلياً بقاعدة البيانات وينفّذ التغييرات)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
