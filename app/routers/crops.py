"""
راوتر المحاصيل وجداول البيانات المرجعية (المحافظات، أنواع التربة، مصادر الري).
هذه المسارات للقراءة فقط — البيانات تُدخل عبر seed السكيما أو لوحة تحكم الأدمن.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Crop, CropSeason, Governorate, SoilType, WaterSource
from app.schemas import CropOut, GovernorateOut, SoilTypeOut, WaterSourceOut

router = APIRouter(prefix="/api", tags=["المحاصيل والبيانات المرجعية - Crops & Lookups"])


@router.get("/crops", response_model=list[CropOut])
def list_crops(
    season: CropSeason | None = None,
    db: Session = Depends(get_db),
):
    """عرض كل المحاصيل، مع إمكانية التصفية حسب الموسم (winter/summer/nili/year)."""
    query = db.query(Crop).filter(Crop.is_active.is_(True))
    if season is not None:
        query = query.filter(Crop.season == season)
    return query.order_by(Crop.name_ar).all()


@router.get("/crops/{crop_code}", response_model=CropOut)
def get_crop(crop_code: str, db: Session = Depends(get_db)):
    """عرض تفاصيل محصول واحد عبر الكود (مثل wheat, corn, rice)."""
    crop = db.query(Crop).filter(Crop.code == crop_code).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المحصول غير موجود")
    return crop


@router.get("/governorates", response_model=list[GovernorateOut])
def list_governorates(db: Session = Depends(get_db)):
    """عرض كل المحافظات المصرية."""
    return db.query(Governorate).order_by(Governorate.name_ar).all()


@router.get("/soil-types", response_model=list[SoilTypeOut])
def list_soil_types(db: Session = Depends(get_db)):
    """عرض كل أنواع التربة المتاحة."""
    return db.query(SoilType).all()


@router.get("/water-sources", response_model=list[WaterSourceOut])
def list_water_sources(db: Session = Depends(get_db)):
    """عرض كل مصادر الري المتاحة."""
    return db.query(WaterSource).all()
