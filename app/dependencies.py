"""
Dependencies مشتركة بين الراوترات: جلسة قاعدة البيانات، استخراج المستخدم الحالي
من JWT Token، والتحقق من الصلاحيات (Roles).
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.security import decode_access_token

# يشير إلى مسار الحصول على التوكن (مستخدم في وثائق Swagger /docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    يفك تشفير التوكن، يستخرج معرف المستخدم (sub)، ويجلبه من قاعدة البيانات.
    يرفع 401 إذا كان التوكن غير صالح أو المستخدم غير موجود أو معطّل.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="بيانات الاعتماد غير صالحة، يرجى تسجيل الدخول مرة أخرى",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_raw)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذا الحساب معطّل")
    return user


def require_roles(*allowed_roles: UserRole):
    """
    مولّد Dependency يقيّد الوصول لمسارات معينة على أدوار محددة فقط.
    مثال الاستخدام: Depends(require_roles(UserRole.admin, UserRole.agronomist))
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="لا تملك الصلاحية الكافية لتنفيذ هذا الإجراء",
            )
        return current_user

    return role_checker
