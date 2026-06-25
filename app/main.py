"""
نقطة الدخول الرئيسية لتطبيق AgriVision Ultra API.
لتشغيل الخادم محلياً: uvicorn app.main:app --reload
"""

import anyio.to_thread
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, ads, auth, crops, farms, feasibility, fertilizer, pests, prices, recommendations, weather
from app.scheduler import shutdown_scheduler, start_scheduler

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "الواجهة البرمجية الخلفية لمنصة AgriVision Ultra للزراعة الذكية: "
        "مصادقة المستخدمين، أسعار السوق، دراسات الجدوى، توصيات الأسمدة، "
        "الطقس، وموسوعة الآفات."
    ),
)

# CORS: يسمح للواجهة الأمامية (مثل agrivision_ultra.html أو تطبيق React/Vue)
# بالاتصال بالـ API من أصل (origin) مختلف أثناء التطوير. يُفضّل تحديد
# نطاقات محددة بدلاً من "*" عند النشر في بيئة الإنتاج.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- تسجيل كل الراوترات -----
app.include_router(auth.router)
app.include_router(farms.router)
app.include_router(crops.router)
app.include_router(prices.router)
app.include_router(feasibility.router)
app.include_router(fertilizer.router)
app.include_router(weather.router)
app.include_router(pests.router)
app.include_router(recommendations.router)
app.include_router(admin.router)
app.include_router(ads.router)


@app.on_event("startup")
def _on_startup():
    """تفعيل الجدولة التلقائية لتحديث الأسعار عند بدء تشغيل الخادم."""
    anyio.to_thread.current_default_thread_limiter().total_tokens = 100
    start_scheduler()


@app.on_event("shutdown")
def _on_shutdown():
    shutdown_scheduler()


@app.get("/", tags=["عام - General"])
def root():
    """نقطة فحص أساسية للتأكد من أن الخادم يعمل."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
    }


@app.get("/health", tags=["عام - General"])
def health_check():
    """نقطة فحص صحة الخادم (Health Check) لاستخدامها مع أدوات المراقبة."""
    return {"status": "healthy"}
