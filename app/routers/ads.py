"""راوتر عام: تقديم الشركات لعروضها/إعلاناتها لمراجعتها من الأدمن لاحقاً."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ad
from app.schemas import AdCreate, AdOut

router = APIRouter(prefix="/api/ads", tags=["الإعلانات - Ads"])


@router.post("", response_model=AdOut, status_code=status.HTTP_201_CREATED)
def submit_ad(payload: AdCreate, db: Session = Depends(get_db)):
    """تقديم طلب عرض/إعلان جديد من شركة. يبقى الطلب 'قيد المراجعة' حتى يوافق عليه الأدمن."""
    ad = Ad(
        company_name=payload.company_name,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        title=payload.title,
        message=payload.message,
    )
    db.add(ad)
    db.commit()
    db.refresh(ad)
    return ad
