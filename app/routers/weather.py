"""
راوتر الطقس: يجلب حالة الطقس الحالية وتوقعات ٧ أيام لمحافظة معيّنة عبر
خدمة Open-Meteo المجانية (لا تتطلب مفتاح API)، ويسجّل كل طلب في weather_logs
لإبقاء سجل تاريخي يمكن الرجوع إليه دون الاعتماد الكامل على الخدمة الخارجية.
"""

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Governorate, WeatherLog
from app.schemas import WeatherCurrentOut, WeatherForecastDayOut, WeatherOut

router = APIRouter(prefix="/api/weather", tags=["الطقس - Weather"])

# تحويل أكواد الطقس الخاصة بـ Open-Meteo (WMO) إلى وصف عربي مبسّط
WMO_CODE_DESCRIPTIONS = {
    0: "صافٍ",
    1: "غالباً صافٍ",
    2: "غائم جزئياً",
    3: "غائم",
    45: "ضباب",
    48: "ضباب متجمد",
    51: "رذاذ خفيف",
    61: "أمطار خفيفة",
    63: "أمطار متوسطة",
    65: "أمطار غزيرة",
    80: "زخات مطر متفرقة",
    95: "عاصفة رعدية",
}


def _describe_weather_code(code: int) -> str:
    return WMO_CODE_DESCRIPTIONS.get(code, "غير محدد")


@router.get("/{governorate_code}", response_model=WeatherOut)
def get_weather(governorate_code: str, db: Session = Depends(get_db)):
    """
    جلب الطقس الحالي وتوقعات ٧ أيام لمحافظة معيّنة عبر إحداثياتها المخزّنة
    في جدول governorates، مع تسجيل القراءة الحالية في weather_logs.
    """
    governorate = db.query(Governorate).filter(Governorate.code == governorate_code).first()
    if not governorate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المحافظة غير موجودة")
    if governorate.latitude is None or governorate.longitude is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا تتوفر إحداثيات جغرافية لهذه المحافظة لجلب الطقس",
        )

    params = {
        "latitude": float(governorate.latitude),
        "longitude": float(governorate.longitude),
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Africa/Cairo",
        "forecast_days": 7,
    }

    try:
        response = httpx.get(settings.OPEN_METEO_BASE_URL, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"تعذّر الاتصال بخدمة الطقس الخارجية: {exc}",
        )

    current = data.get("current", {})
    daily = data.get("daily", {})

    weather_code = int(current.get("weather_code", 0))
    condition_text = _describe_weather_code(weather_code)
    temperature = float(current.get("temperature_2m", 0))
    humidity = float(current.get("relative_humidity_2m", 0))
    wind_speed = float(current.get("wind_speed_10m", 0))

    # تسجيل القراءة الحالية كسجل تاريخي
    log_entry = WeatherLog(
        governorate_id=governorate.id,
        temperature=temperature,
        humidity=humidity,
        wind_speed=wind_speed,
        condition_text=condition_text,
    )
    db.add(log_entry)
    db.commit()

    forecast_days = []
    dates = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    rainfalls = daily.get("precipitation_sum", [])
    for i in range(len(dates)):
        forecast_days.append(
            WeatherForecastDayOut(
                date=dates[i],
                max_temp=max_temps[i] if i < len(max_temps) else 0,
                min_temp=min_temps[i] if i < len(min_temps) else 0,
                rainfall_mm=rainfalls[i] if i < len(rainfalls) else 0,
            )
        )

    return WeatherOut(
        current=WeatherCurrentOut(
            governorate_code=governorate.code,
            governorate_name_ar=governorate.name_ar,
            temperature=temperature,
            humidity=humidity,
            wind_speed=wind_speed,
            condition_text=condition_text,
            recorded_at=datetime.now(timezone.utc),
        ),
        forecast=forecast_days,
    )
