"""
المهام المجدولة التلقائية لتطبيق AgriVision Ultra.
حالياً: تحديث يومي لأسعار السوق (محاكاة ذكية) بدون أي تدخل بشري.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.routers.prices import run_daily_price_simulation

logger = logging.getLogger("agrivision.scheduler")

scheduler = BackgroundScheduler(timezone="Africa/Cairo")


def _job_daily_price_update():
    """تُنفَّذ تلقائياً كل يوم: تحدّث أسعار جميع المحاصيل النشطة بمنطق المحاكاة الذكية."""
    db = SessionLocal()
    try:
        results = run_daily_price_simulation(db)
        logger.info("تحديث الأسعار اليومي التلقائي تم بنجاح لعدد %d محصول", len(results))
    except Exception:
        logger.exception("فشل تحديث الأسعار اليومي التلقائي")
    finally:
        db.close()


def start_scheduler():
    """يُستدعى عند بدء تشغيل الخادم (startup) لتفعيل الجدولة إن لم تكن مفعّلة."""
    if not scheduler.running:
        scheduler.add_job(
            _job_daily_price_update,
            trigger="cron",
            hour=6,
            minute=0,
            id="daily_price_update",
            replace_existing=True,
            misfire_grace_time=3600,
        )
        scheduler.start()
        logger.info("تم تفعيل الجدولة التلقائية لتحديث الأسعار (يومياً 6:00 صباحاً بتوقيت القاهرة)")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)