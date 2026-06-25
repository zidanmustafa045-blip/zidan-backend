"""
الاتصال بقاعدة البيانات PostgreSQL باستخدام SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# pool_pre_ping=True يتأكد من صلاحية الاتصال قبل كل استعلام (مفيد مع اتصالات قد تنقطع)
# ملاحظة هامة (إصلاح اختناق التزامن): DATABASE_URL يجب أن يشير لمنفذ Supavisor
# في وضع transaction mode (port 6543) لا session mode (port 5432)، لأن session
# mode على Supabase محدود بعدد قليل من الاتصالات المتزامنة (15 فقط هنا) وكان
# هذا هو السبب الجذري لفشل تسجيل عشرات المستخدمين في نفس اللحظة (500 errors).
# في transaction mode يستطيع الـ pooler التعامل مع مئات العملاء المتزامنين.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
    pool_timeout=10,
    pool_recycle=300,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency تُستخدم في كل راوتر للحصول على جلسة قاعدة بيانات،
    وتُغلق الجلسة تلقائياً بعد انتهاء الطلب.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
