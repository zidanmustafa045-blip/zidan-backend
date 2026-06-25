"""
راوتر موسوعة الآفات وكشف الآفات بالصور.

ملاحظة هامة عن /detect: هذا المسار في نسخته الحالية يستخدم منطق اختيار
مبسّط (placeholder) بدلاً من نموذج رؤية حاسوبية حقيقي، لأن تدريب/استدعاء
نموذج تصنيف صور فعلي يخرج عن نطاق هذا الـ Backend الأساسي. الهيكلة (حفظ
الصورة، تسجيل النتيجة في pest_detections، إرجاع نسبة ثقة) جاهزة بالكامل
لاستبدال المنطق المبسّط بنموذج ML حقيقي (مثل TensorFlow/PyTorch) دون أي
تغيير في شكل الـ API الذي يتعامل معه العميل (Frontend).
"""

import random
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Crop, Pest, PestDetection, User
from app.schemas import PestDetectionOut, PestOut

router = APIRouter(prefix="/api/pests", tags=["الآفات - Pests"])

UPLOAD_DIR = Path("uploads/pest_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5MB، كما هو محدد في واجهة الرفع


@router.get("", response_model=list[PestOut])
def list_pests(db: Session = Depends(get_db)):
    """عرض موسوعة الآفات والأمراض الكاملة."""
    return db.query(Pest).order_by(Pest.name_ar).all()


@router.get("/{pest_id}", response_model=PestOut)
def get_pest(pest_id: int, db: Session = Depends(get_db)):
    """عرض تفاصيل آفة معيّنة: الأعراض والحل المقترح."""
    pest = db.query(Pest).filter(Pest.id == pest_id).first()
    if not pest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الآفة غير موجودة")
    return pest


@router.post("/detect", response_model=PestDetectionOut, status_code=status.HTTP_201_CREATED)
def detect_pest(
    image: UploadFile = File(...),
    crop_code: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    رفع صورة ورقة مصابة لكشف الآفة المحتملة. يحفظ الصورة على القرص ويسجّل
    نتيجة الكشف في pest_detections مع نسبة ثقة تقديرية.
    """
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="صيغة الصورة غير مدعومة، يُسمح فقط بـ JPG و PNG",
        )

    file_extension = Path(image.filename or "image.jpg").suffix or ".jpg"
    stored_filename = f"{uuid.uuid4()}{file_extension}"
    destination_path = UPLOAD_DIR / stored_filename

    with destination_path.open("wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    if destination_path.stat().st_size > MAX_UPLOAD_SIZE_BYTES:
        destination_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="حجم الصورة يتجاوز 5MB")

    crop = None
    if crop_code:
        crop = db.query(Crop).filter(Crop.code == crop_code).first()

    # --- منطق مبسّط لاختيار آفة محتملة (placeholder لنموذج رؤية حاسوبية حقيقي) ---
    all_pests = db.query(Pest).all()
    if not all_pests:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="لا توجد بيانات آفات مسجّلة بعد")
    predicted_pest = random.choice(all_pests)
    confidence = round(random.uniform(65, 96), 2)

    detection = PestDetection(
        user_id=current_user.id,
        crop_id=crop.id if crop else None,
        pest_id=predicted_pest.id,
        image_url=str(destination_path),
        confidence=confidence,
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)
    return detection
