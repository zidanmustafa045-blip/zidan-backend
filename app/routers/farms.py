"""
راوتر المزارع: إنشاء وعرض وحذف المزارع الخاصة بالمستخدم الحالي.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Farm, User
from app.schemas import FarmCreate, FarmOut

router = APIRouter(prefix="/api/farms", tags=["المزارع - Farms"])


@router.post("", response_model=FarmOut, status_code=status.HTTP_201_CREATED)
def create_farm(
    payload: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """إنشاء مزرعة جديدة مرتبطة بالمستخدم الحالي."""
    farm = Farm(
        user_id=current_user.id,
        name=payload.name,
        governorate_id=payload.governorate_id,
        soil_type_id=payload.soil_type_id,
        water_source_id=payload.water_source_id,
        area_feddan=payload.area_feddan,
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("", response_model=list[FarmOut])
def list_my_farms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """عرض كل المزارع الخاصة بالمستخدم الحالي."""
    return db.query(Farm).filter(Farm.user_id == current_user.id).order_by(Farm.created_at.desc()).all()


@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(
    farm_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """عرض تفاصيل مزرعة محددة، يجب أن تنتمي للمستخدم الحالي."""
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == current_user.id).first()
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المزرعة غير موجودة")
    return farm


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(
    farm_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """حذف مزرعة تابعة للمستخدم الحالي."""
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.user_id == current_user.id).first()
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المزرعة غير موجودة")
    db.delete(farm)
    db.commit()
    return None
