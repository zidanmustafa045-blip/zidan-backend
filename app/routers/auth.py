"""
راوتر المصادقة: تسجيل مستخدم جديد، تسجيل الدخول، وجلب بيانات المستخدم الحالي.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, UserRole
from app.schemas import Token, UserCreate, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["المصادقة - Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    تسجيل مستخدم جديد. يرفض الطلب إذا كان البريد الإلكتروني مستخدماً من قبل.
    """
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="هذا البريد الإلكتروني مسجل مسبقاً",
        )

    new_user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=UserRole.farmer,  # hard-coded: public registration can never self-assign a role
        governorate_id=payload.governorate_id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    تسجيل الدخول باستخدام البريد الإلكتروني وكلمة المرور (حقل username في النموذج = البريد الإلكتروني).
    يُعيد JWT Access Token صالحاً مع بيانات المستخدم.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="البريد الإلكتروني أو كلمة المرور غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذا الحساب معطّل")

    access_token = create_access_token(data={"sub": str(user.id)})

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return Token(access_token=access_token, user=user)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """إرجاع بيانات المستخدم الحالي بناءً على التوكن المُرسل في الهيدر Authorization."""
    return current_user
