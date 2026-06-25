"""
راوتر توصية المحصول الذكية بناءً على قيم NPK والمناخ (مطابق لقسم
"توصية المحصول" في الواجهة — دالة getRec()). يستخدم منطق تقارب مبسّط
(rule-based) بين مدخلات المستخدم ومتطلبات كل محصول، ويُمكن استبداله لاحقاً
بنموذج تعلم آلي مدرّب على بيانات NPK الحقيقية دون تغيير شكل الـ API.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Crop, CropRecommendation, CropSeason, User
from app.schemas import CropRecommendationIn, CropRecommendationOut

router = APIRouter(prefix="/api/recommendations", tags=["توصية المحصول - Crop Recommendation"])

# تقدير تقريبي لدرجة الحرارة المثلى ومتطلبات الرطوبة لكل موسم زراعي
SEASON_PROFILE = {
    CropSeason.winter: {"temp": 18, "humidity": 55, "rain": 80},
    CropSeason.summer: {"temp": 32, "humidity": 60, "rain": 40},
    CropSeason.nili: {"temp": 28, "humidity": 65, "rain": 120},
    CropSeason.year: {"temp": 25, "humidity": 60, "rain": 100},
}


@router.post("", response_model=CropRecommendationOut)
def recommend_crop(
    payload: CropRecommendationIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    يقترح المحصول الأنسب بناءً على قيم النيتروجين والفوسفور والبوتاسيوم
    ودرجة الحرارة والرطوبة وكمية الأمطار، عبر حساب درجة تقارب بسيطة بين
    مدخلات المستخدم ومتوسط متطلبات كل موسم زراعي للمحاصيل المتاحة.
    """
    crops = db.query(Crop).filter(Crop.is_active.is_(True)).all()
    if not crops:
        return CropRecommendationOut(
            recommended_crop_code=None,
            recommended_crop_name_ar=None,
            confidence=0,
            explanation="لا توجد محاصيل مسجّلة بعد لإجراء التوصية.",
        )

    best_crop = None
    best_score = -1.0

    for crop in crops:
        profile = SEASON_PROFILE[crop.season]
        # حساب درجة تقارب عكسية بسيطة: كل ما قلّ الفرق بين المدخلات والمتطلبات، زادت الدرجة
        temp_diff = abs(payload.temperature - profile["temp"])
        humidity_diff = abs(payload.humidity - profile["humidity"])
        rain_diff = abs(payload.rainfall_mm - profile["rain"])

        score = 100 - (temp_diff * 1.5 + humidity_diff * 0.8 + rain_diff * 0.1)
        score = max(0.0, min(100.0, score))

        if score > best_score:
            best_score = score
            best_crop = crop

    recommendation_log = CropRecommendation(
        user_id=current_user.id,
        nitrogen=payload.nitrogen,
        phosphorus=payload.phosphorus,
        potassium=payload.potassium,
        temperature=payload.temperature,
        humidity=payload.humidity,
        rainfall_mm=payload.rainfall_mm,
        recommended_crop_id=best_crop.id if best_crop else None,
        confidence=round(best_score, 2),
    )
    db.add(recommendation_log)
    db.commit()

    explanation = (
        f"بناءً على درجة الحرارة ({payload.temperature}°C) والرطوبة ({payload.humidity}%) "
        f"وكمية الأمطار ({payload.rainfall_mm}مم)، يُعتبر محصول {best_crop.name_ar} "
        f"الأكثر توافقاً مع هذه الظروف المناخية بنسبة تقارب {round(best_score, 1)}%."
    )

    return CropRecommendationOut(
        recommended_crop_code=best_crop.code,
        recommended_crop_name_ar=best_crop.name_ar,
        confidence=round(best_score, 2),
        explanation=explanation,
    )
