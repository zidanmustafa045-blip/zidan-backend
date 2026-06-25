"""راوتر لوحة تحكم الأدمن: إحصائيات، إدارة المستخدمين، ومراجعة عروض الشركات (الإعلانات)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import Ad, User, UserRole
from app.schemas import AdOut, AdUpdateByAdmin, AdminStatsOut, UserOut, UserUpdateByAdmin

router = APIRouter(prefix="/api/admin", tags=["الأدمن - Admin"])

admin_only = require_roles(UserRole.admin)


@router.get("/stats", response_model=AdminStatsOut)
def get_stats(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    """إحصائيات عامة: عدد المستخدمين، حالتهم، وعدد الإعلانات."""
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    inactive_users = total_users - active_users

    role_rows = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    users_by_role = {role.value: count for role, count in role_rows}

    total_ads = db.query(func.count(Ad.id)).scalar() or 0
    pending_ads = db.query(func.count(Ad.id)).filter(Ad.status == "pending").scalar() or 0

    return AdminStatsOut(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        users_by_role=users_by_role,
        total_ads=total_ads,
        pending_ads=pending_ads,
    )


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    """إرجاع كل المستخدمين المسجلين في النظام."""
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateByAdmin,
    db: Session = Depends(get_db),
    current_admin: User = Depends(admin_only),
):
    """تفعيل/تعطيل مستخدم أو تغيير صلاحيته (role)."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المستخدم غير موجود")

    if user.id == current_admin.id and payload.is_active is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="لا يمكنك تعطيل حسابك الخاص")
    if user.id == current_admin.id and payload.role is not None and payload.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="لا يمكنك إزالة صلاحية الأدمن عن حسابك الخاص")

    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role is not None:
        user.role = payload.role

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(admin_only),
):
    """حذف مستخدم نهائياً من قاعدة البيانات."""
    if user_id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="لا يمكنك حذف حسابك الخاص")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المستخدم غير موجود")

    db.delete(user)
    db.commit()
    return None


@router.get("/ads", response_model=list[AdOut])
def list_ads(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    """إرجاع كل طلبات/عروض الشركات (الإعلانات) لمراجعتها."""
    return db.query(Ad).order_by(Ad.created_at.desc()).all()


@router.patch("/ads/{ad_id}", response_model=AdOut)
def update_ad(
    ad_id: uuid.UUID,
    payload: AdUpdateByAdmin,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    """قبول أو رفض عرض شركة معينة، مع إمكانية إضافة ملاحظة من الأدمن."""
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if ad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الإعلان غير موجود")

    if payload.status is not None:
        ad.status = payload.status
    if payload.admin_note is not None:
        ad.admin_note = payload.admin_note

    db.commit()
    db.refresh(ad)
    return ad


@router.delete("/ads/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ad(ad_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    """حذف طلب إعلان نهائياً."""
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if ad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الإعلان غير موجود")
    db.delete(ad)
    db.commit()
    return None
