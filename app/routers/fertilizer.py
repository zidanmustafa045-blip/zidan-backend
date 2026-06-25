"""
راوتر حاسبة السماد الذكية: عرض التوصية القياسية لكل محصول، وحساب جرعة
مخصصة بناءً على عمر النبات ولون الأوراق ونوع التربة (مطابق لـ calcFert() بالواجهة).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Crop, FertilizerCalculation, FertilizerRecommendation, SoilType, User
from app.schemas import FertilizerCalculateIn, FertilizerCalculateOut, FertilizerRecommendationOut

router = APIRouter(prefix="/api/fertilizer", tags=["الأسمدة - Fertilizer"])

# معاملات تعديل الجرعة بحسب لون الأوراق (مؤشر على نقص عنصر معيّن)
# أصفر فاتح => نقص نيتروجين، أرجواني => نقص فوسفور، بني جاف => نقص بوتاسيوم
LEAF_COLOR_ADJUSTMENTS = {
    "green": {"n": 1.0, "p": 1.0, "k": 1.0, "note": "لون الأوراق طبيعي، لا حاجة لتعديل الجرعة القياسية."},
    "yellow": {"n": 1.20, "p": 1.0, "k": 1.0, "note": "اصفرار الأوراق يشير لاحتمال نقص النيتروجين، تمت زيادة جرعته 20%."},
    "brown": {"n": 1.0, "p": 1.0, "k": 1.25, "note": "جفاف وبنية الأوراق قد يشير لنقص البوتاسيوم، تمت زيادة جرعته 25%."},
    "purple": {"n": 1.0, "p": 1.25, "k": 1.0, "note": "الاحمرار/الاصفرار الأرجواني يشير لنقص الفوسفور، تمت زيادة جرعته 25%."},
    "spotted": {"n": 1.10, "p": 1.10, "k": 1.10, "note": "التبقع قد يشير لخلل تغذوي عام، تمت زيادة الجرعة الكلية 10% مع مراجعة الآفات."},
}

# معاملات تعديل بحسب نوع التربة (التربة الرملية تحتاج جرعات أكثر تكراراً لضعف احتفاظها بالعناصر)
SOIL_ADJUSTMENTS = {
    "sandy": 1.15,
    "clay": 0.95,
    "silty": 1.0,
    "loamy": 1.05,
    "peat": 0.90,
    "chalk": 1.10,
}


@router.get("/recommendations/{crop_code}", response_model=FertilizerRecommendationOut)
def get_fertilizer_recommendation(crop_code: str, db: Session = Depends(get_db)):
    """عرض التوصية القياسية للسماد لمحصول معيّن (النوع، الكمية للفدان، التوقيت، وقيم NPK)."""
    crop = db.query(Crop).filter(Crop.code == crop_code).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المحصول غير موجود")

    recommendation = (
        db.query(FertilizerRecommendation).filter(FertilizerRecommendation.crop_id == crop.id).first()
    )
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لا توجد توصية سماد مسجّلة لهذا المحصول",
        )
    return recommendation


@router.post("/calculate", response_model=FertilizerCalculateOut)
def calculate_fertilizer_dose(
    payload: FertilizerCalculateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    حساب جرعة سماد مخصصة بناءً على المحصول وعمره ولون أوراقه ونوع التربة،
    وحفظ سجل الحساب في fertilizer_calculations.
    """
    crop = db.query(Crop).filter(Crop.code == payload.crop_code).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المحصول غير موجود")

    base_recommendation = (
        db.query(FertilizerRecommendation).filter(FertilizerRecommendation.crop_id == crop.id).first()
    )
    if not base_recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لا توجد توصية سماد أساسية لهذا المحصول لإجراء الحساب",
        )

    color_factor = LEAF_COLOR_ADJUSTMENTS.get(payload.leaf_color, LEAF_COLOR_ADJUSTMENTS["green"])

    soil_code = None
    if payload.soil_type_id is not None:
        soil = db.query(SoilType).filter(SoilType.id == payload.soil_type_id).first()
        soil_code = soil.code if soil else None
    soil_factor = SOIL_ADJUSTMENTS.get(soil_code, 1.0)

    recommended_n = round(base_recommendation.n_value * color_factor["n"] * soil_factor)
    recommended_p = round(base_recommendation.p_value * color_factor["p"] * soil_factor)
    recommended_k = round(base_recommendation.k_value * color_factor["k"] * soil_factor)

    calculation_log = FertilizerCalculation(
        user_id=current_user.id,
        crop_id=crop.id,
        crop_age_days=payload.crop_age_days,
        leaf_color=payload.leaf_color,
        soil_type_id=payload.soil_type_id,
        recommended_n=recommended_n,
        recommended_p=recommended_p,
        recommended_k=recommended_k,
    )
    db.add(calculation_log)
    db.commit()

    return FertilizerCalculateOut(
        crop_code=crop.code,
        fertilizer_type=base_recommendation.fertilizer_type,
        amount_per_feddan=base_recommendation.amount_per_feddan,
        timing=base_recommendation.timing,
        recommended_n=recommended_n,
        recommended_p=recommended_p,
        recommended_k=recommended_k,
        notes=color_factor["note"],
    )
