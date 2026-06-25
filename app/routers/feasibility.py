"""
راوتر دراسة الجدوى الذكية: استقبال بيانات المحصول والمساحة والتكاليف،
حساب الإنتاج والإيرادات والربح الصافي والعائد على الاستثمار ومدة الاسترداد،
وحفظ النتيجة كاملة في قاعدة البيانات.

منطق الحساب مطابق لدالة calcFeas() في الواجهة الأمامية (agrivision_ultra.html):
- إجمالي التكلفة = مجموع بنود التكاليف الثابتة + المتغيرة، أو (تكلفة الفدان
  الافتراضية للمحصول × المساحة) في حال عدم إدخال أي بنود تكلفة.
- الإنتاج المتوقع (كجم) = الإنتاجية المتوسطة للفدان (طن) × المساحة × 1000.
- الإيرادات = الإنتاج (كجم) × سعر الكيلوجرام الحالي (آخر سعر مسجل، أو السعر
  الأساسي للمحصول إن لم يوجد سعر مسجل).
- صافي الربح = الإيرادات - إجمالي التكلفة.
- العائد على الاستثمار = (صافي الربح / إجمالي التكلفة) × 100.
- مدة الاسترداد بالشهور = إجمالي التكلفة ÷ (صافي الربح ÷ 12) إذا كان الربح موجباً.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import (
    Crop,
    CropDailyPrice,
    FeasibilityCostItem,
    FeasibilityResult,
    FeasibilityStatus,
    FeasibilityStudy,
    User,
)
from app.schemas import FeasibilityCreate, FeasibilityStudyOut

router = APIRouter(prefix="/api/feasibility", tags=["دراسة الجدوى - Feasibility Studies"])


def _get_current_crop_price(db: Session, crop: Crop) -> float:
    """يجلب آخر سعر مسجّل للمحصول، أو يعود للسعر الأساسي إذا لم يوجد سعر محدّث."""
    latest_price = (
        db.query(CropDailyPrice)
        .filter(CropDailyPrice.crop_id == crop.id)
        .order_by(desc(CropDailyPrice.price_date))
        .first()
    )
    return float(latest_price.price) if latest_price else float(crop.base_price)


def _calculate_and_persist_result(db: Session, study: FeasibilityStudy, crop: Crop) -> FeasibilityResult:
    """ينفّذ كل حسابات الجدوى المالية للدراسة ويخزّن النتيجة في feasibility_results."""
    cost_items = study.cost_items
    total_fixed = sum(float(item.amount) for item in cost_items if item.cost_type.value == "fixed")
    total_variable = sum(float(item.amount) for item in cost_items if item.cost_type.value == "variable")
    total_cost = total_fixed + total_variable

    area = float(study.area_feddan)
    if total_cost <= 0:
        # في حال عدم إدخال أي بنود تكلفة، نستخدم التكلفة التقديرية الافتراضية للمحصول
        total_cost = float(crop.avg_cost_feddan) * area
        total_variable = total_cost  # تُعامل كتكلفة متغيرة تقديرية

    cost_per_feddan = total_cost / area if area > 0 else 0

    current_price = _get_current_crop_price(db, crop)
    expected_production_kg = float(crop.avg_yield_ton_feddan) * area * 1000
    expected_revenue = expected_production_kg * current_price
    net_profit = expected_revenue - total_cost

    roi_percent = (net_profit / total_cost * 100) if total_cost > 0 else 0
    payback_months = (total_cost / (net_profit / 12)) if net_profit > 0 else None
    is_profitable = net_profit > 0

    if is_profitable:
        recommendation = (
            f"✅ المشروع مربح: يُنصح بالمضي قدماً في زراعة {crop.name_ar}. "
            f"الإيرادات المتوقعة ({round(expected_revenue):,} ج.م) تتجاوز التكاليف "
            f"({round(total_cost):,} ج.م) بعائد استثمار {round(roi_percent, 1)}%."
        )
    else:
        recommendation = (
            f"⚠️ يحتاج المشروع لمراجعة: التكاليف الحالية ({round(total_cost):,} ج.م) "
            f"تتجاوز أو تقارب الإيرادات المتوقعة ({round(expected_revenue):,} ج.م). "
            "يُنصح بمراجعة التكاليف أو دراسة محصول بديل أعلى ربحية."
        )

    result = study.result
    if result is None:
        result = FeasibilityResult(study_id=study.id)
        db.add(result)

    result.total_fixed_cost = round(total_fixed, 2)
    result.total_variable_cost = round(total_variable, 2)
    result.total_cost = round(total_cost, 2)
    result.cost_per_feddan = round(cost_per_feddan, 2)
    result.expected_production_kg = round(expected_production_kg, 2)
    result.expected_revenue = round(expected_revenue, 2)
    result.net_profit = round(net_profit, 2)
    result.roi_percent = round(roi_percent, 2)
    result.payback_months = round(payback_months, 1) if payback_months is not None else None
    result.is_profitable = is_profitable
    result.ai_recommendation = recommendation

    return result


@router.post("", response_model=FeasibilityStudyOut, status_code=status.HTTP_201_CREATED)
def create_feasibility_study(
    payload: FeasibilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    إنشاء دراسة جدوى جديدة كاملة: المعلومات الأساسية + بنود التكاليف،
    مع حساب النتيجة المالية فوراً وحفظها.
    """
    crop = db.query(Crop).filter(Crop.code == payload.crop_code).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المحصول غير موجود")

    study = FeasibilityStudy(
        user_id=current_user.id,
        crop_id=crop.id,
        governorate_id=payload.governorate_id,
        soil_type_id=payload.soil_type_id,
        water_source_id=payload.water_source_id,
        season=payload.season,
        area_feddan=payload.area_feddan,
        status=FeasibilityStatus.completed,
    )
    db.add(study)
    db.flush()  # لضمان توليد study.id قبل إضافة بنود التكاليف

    for item in payload.cost_items:
        db.add(
            FeasibilityCostItem(
                study_id=study.id,
                cost_type=item.cost_type,
                category=item.category,
                amount=item.amount,
            )
        )
    db.flush()
    db.refresh(study)  # لإعادة تحميل علاقة cost_items بعد الإضافة

    _calculate_and_persist_result(db, study, crop)
    db.commit()
    db.refresh(study)
    return study


@router.get("", response_model=list[FeasibilityStudyOut])
def list_my_feasibility_studies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """عرض كل دراسات الجدوى الخاصة بالمستخدم الحالي، الأحدث أولاً."""
    return (
        db.query(FeasibilityStudy)
        .options(joinedload(FeasibilityStudy.cost_items), joinedload(FeasibilityStudy.result))
        .filter(FeasibilityStudy.user_id == current_user.id)
        .order_by(FeasibilityStudy.created_at.desc())
        .all()
    )


@router.get("/{study_id}", response_model=FeasibilityStudyOut)
def get_feasibility_study(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """عرض تفاصيل دراسة جدوى محددة مع بنود التكاليف والنتيجة المالية."""
    study = (
        db.query(FeasibilityStudy)
        .options(joinedload(FeasibilityStudy.cost_items), joinedload(FeasibilityStudy.result))
        .filter(FeasibilityStudy.id == study_id, FeasibilityStudy.user_id == current_user.id)
        .first()
    )
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="دراسة الجدوى غير موجودة")
    return study


@router.delete("/{study_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feasibility_study(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """حذف دراسة جدوى (وكل بنود تكاليفها ونتيجتها تبعاً للـ CASCADE)."""
    study = (
        db.query(FeasibilityStudy)
        .filter(FeasibilityStudy.id == study_id, FeasibilityStudy.user_id == current_user.id)
        .first()
    )
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="دراسة الجدوى غير موجودة")
    db.delete(study)
    db.commit()
    return None
