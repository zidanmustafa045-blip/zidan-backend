"""
ط±ط§ظˆطھط± ط£ط³ط¹ط§ط± ط§ظ„ط³ظˆظ‚ ط§ظ„ظٹظˆظ…ظٹط©: ط¬ظ„ط¨ ط¢ط®ط± ط³ط¹ط± ظ„ظƒظ„ ظ…ط­طµظˆظ„طŒ ط¬ظ„ط¨ ط§ظ„ط³ط¬ظ„ ط§ظ„طھط§ط±ظٹط®ظٹطŒ
ط¥ط¶ط§ظپط©/طھط­ط¯ظٹط« ط³ط¹ط± ط§ظ„ظٹظˆظ…طŒ ظˆطھط­ط¯ظٹط« ط¬ظ…ط§ط¹ظٹ (refresh) ظ„ظ…ط­ط§ظƒط§ط© طھط؛ظٹظ‘ط± ط§ظ„ط³ظˆظ‚.
"""

import random
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import Crop, CropDailyPrice, MarketStatus, PriceTrend, UserRole
from app.schemas import CropPriceCreate, CropPriceOut, CropPriceWithCropOut

router = APIRouter(prefix="/api/prices", tags=["ط£ط³ط¹ط§ط± ط§ظ„ط³ظˆظ‚ - Market Prices"])


def _build_price_with_crop(price: CropDailyPrice) -> CropPriceWithCropOut:
    return CropPriceWithCropOut(
        id=price.id,
        crop_id=price.crop_id,
        price_date=price.price_date,
        price=float(price.price),
        change_percent=float(price.change_percent),
        trend=price.trend,
        high_price=float(price.high_price) if price.high_price is not None else None,
        low_price=float(price.low_price) if price.low_price is not None else None,
        status=price.status,
        crop_code=price.crop.code,
        crop_name_ar=price.crop.name_ar,
        crop_emoji=price.crop.emoji,
    )


@router.get("", response_model=list[CropPriceWithCropOut])
def list_latest_prices(db: Session = Depends(get_db)):
    """
    ط¥ط±ط¬ط§ط¹ ط¢ط®ط± ط³ط¹ط± ظ…ط³ط¬ظ‘ظ„ ظ„ظƒظ„ ظ…ط­طµظˆظ„ (ظ…ط·ط§ط¨ظ‚ ظ„طھط¨ظˆظٹط¨ "ط£ط³ط¹ط§ط± ط§ظ„ط³ظˆظ‚" ظپظٹ ط§ظ„ظˆط§ط¬ظ‡ط©).
    ط¥ط°ط§ ظ„ظ… ظٹظˆط¬ط¯ ط³ط¹ط± ظ…ط³ط¬ظ‘ظ„ ظ„ظ…ط­طµظˆظ„طŒ ظٹطھظ… طھط¬ط§ظ‡ظ„ظ‡ ظ…ظ† ط§ظ„ظ‚ط§ط¦ظ…ط©.
    """
    crops = db.query(Crop).filter(Crop.is_active.is_(True)).all()
    results: list[CropPriceWithCropOut] = []
    for crop in crops:
        latest_price = (
            db.query(CropDailyPrice)
            .filter(CropDailyPrice.crop_id == crop.id)
            .order_by(desc(CropDailyPrice.price_date))
            .first()
        )
        if latest_price:
            results.append(_build_price_with_crop(latest_price))
    return results


@router.get("/{crop_code}", response_model=list[CropPriceOut])
def get_price_history(
    crop_code: str,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """ط¬ظ„ط¨ ط§ظ„ط³ط¬ظ„ ط§ظ„طھط§ط±ظٹط®ظٹ ظ„ط£ط³ط¹ط§ط± ظ…ط­طµظˆظ„ ظ…ط¹ظٹظ‘ظ† ط®ظ„ط§ظ„ ط¹ط¯ط¯ ط§ظ„ط£ظٹط§ظ… ط§ظ„ظ…ط­ط¯ط¯ (ط§ظپطھط±ط§ط¶ظٹط§ظ‹ 30 ظٹظˆظ…)."""
    crop = db.query(Crop).filter(Crop.code == crop_code).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ط§ظ„ظ…ط­طµظˆظ„ ط؛ظٹط± ظ…ظˆط¬ظˆط¯")

    since_date = date.today() - timedelta(days=days)
    history = (
        db.query(CropDailyPrice)
        .filter(CropDailyPrice.crop_id == crop.id, CropDailyPrice.price_date >= since_date)
        .order_by(CropDailyPrice.price_date)
        .all()
    )
    return history


@router.post(
    "",
    response_model=CropPriceOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.agronomist))],
)
def upsert_today_price(payload: CropPriceCreate, db: Session = Depends(get_db)):
    """
    ط¥ط¶ط§ظپط© ط£ظˆ طھط­ط¯ظٹط« ط³ط¹ط± ط§ظ„ظٹظˆظ… ظ„ظ…ط­طµظˆظ„ ظ…ط¹ظٹظ‘ظ† (ظ…ط³ظ…ظˆط­ ظپظ‚ط· ظ„ظ„ط£ط¯ظ…ظ† ظˆط®ط¨ظٹط± ط§ظ„ط²ط±ط§ط¹ط©).
    ظٹط­ط¯ط¯ ط­ط§ظ„ط© ط§ظ„ط³ظˆظ‚ (ظ…ظ…طھط§ط²/ظ…ط³طھظ‚ط±/ط­ط°ط±) طھظ„ظ‚ط§ط¦ظٹط§ظ‹ ط¨ظ†ط§ط،ظ‹ ط¹ظ„ظ‰ ظ†ط³ط¨ط© ط§ظ„طھط؛ظٹظ‘ط±.
    """
    crop = db.query(Crop).filter(Crop.code == payload.crop_code).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ط§ظ„ظ…ط­طµظˆظ„ ط؛ظٹط± ظ…ظˆط¬ظˆط¯")

    price_date = payload.price_date or date.today()
    trend = PriceTrend.up if payload.change_percent > 0 else (
        PriceTrend.down if payload.change_percent < 0 else PriceTrend.stable
    )
    market_status = (
        MarketStatus.excellent
        if payload.change_percent > 5
        else MarketStatus.caution if payload.change_percent < -5 else MarketStatus.stable
    )

    existing = (
        db.query(CropDailyPrice)
        .filter(CropDailyPrice.crop_id == crop.id, CropDailyPrice.price_date == price_date)
        .first()
    )
    if existing:
        existing.price = payload.price
        existing.change_percent = payload.change_percent
        existing.trend = trend
        existing.high_price = payload.high_price
        existing.low_price = payload.low_price
        existing.status = market_status
        db.commit()
        db.refresh(existing)
        return existing

    new_price = CropDailyPrice(
        crop_id=crop.id,
        price_date=price_date,
        price=payload.price,
        change_percent=payload.change_percent,
        trend=trend,
        high_price=payload.high_price,
        low_price=payload.low_price,
        status=market_status,
        source="manual",
    )
    db.add(new_price)
    db.commit()
    db.refresh(new_price)
    return new_price


def run_daily_price_simulation(db: Session) -> list[CropPriceWithCropOut]:
    """
    ظ…ط­ط§ظƒط§ط© ط°ظƒظٹط© ظ„طھط­ط¯ظٹط« ط£ط³ط¹ط§ط± ط§ظ„ظٹظˆظ… ظ„ظƒظ„ ط§ظ„ظ…ط­ط§طµظٹظ„: طھط¹طھظ…ط¯ ط¹ظ„ظ‰ ط¢ط®ط± ط³ط¹ط± ظ…ط³ط¬ظ„ ظپط¹ظ„ظٹط§ظ‹
    (ط§ط³طھظ…ط±ط§ط±ظٹط© / random walk) ظ…ط¹ ط§ظ†ط¬ط°ط§ط¨ طھط¯ط±ظٹط¬ظٹ ظ†ط­ظˆ ط§ظ„ط³ط¹ط± ط§ظ„ط£ط³ط§ط³ظٹ (mean reversion)
    ظˆط²ط®ظ… ط§طھط¬ط§ظ‡ظٹ (momentum) ظٹط¬ط¹ظ„ ط§ط­طھظ…ط§ظ„ ط§ط³طھظ…ط±ط§ط± ط§طھط¬ط§ظ‡ ط§ظ„ط£ظ…ط³ ط£ط¹ظ„ظ‰ ظ…ظ† ط§ظ†ط¹ظƒط§ط³ظ‡ ط§ظ„ظ…ظپط§ط¬ط¦طŒ
    ط¨ط¯ظ„ط§ظ‹ ظ…ظ† ط§ظ„ظ‚ظپط² ط§ظ„ط¹ط´ظˆط§ط¦ظٹ ط­ظˆظ„ ط§ظ„ط³ط¹ط± ط§ظ„ط£ط³ط§ط³ظٹ ظپظٹ ظƒظ„ طھط­ط¯ظٹط« (ط§ظ„ط£ظ‚ط±ط¨ ظ„ط³ظ„ظˆظƒ ط³ظˆظ‚ ط­ظ‚ظٹظ‚ظٹ).
    طھظڈط³طھط®ط¯ظ… ظ‡ط°ظ‡ ط§ظ„ط¯ط§ظ„ط© ظ…ظ† ط§ظ„ظ…ظ‡ظ…ط© ط§ظ„ظ…ط¬ط¯ظˆظ„ط© ط§ظ„ظٹظˆظ…ظٹط© ط§ظ„طھظ„ظ‚ط§ط¦ظٹط© (scheduler) ظˆظ…ظ† ظ†ظ‚ط·ط©
    /api/prices/refresh ط§ظ„ظٹط¯ظˆظٹط© ظ„ظ„ط£ط¯ظ…ظ†/ط®ط¨ظٹط± ط§ظ„ط²ط±ط§ط¹ط©.
    """
    crops = db.query(Crop).filter(Crop.is_active.is_(True)).all()
    today = date.today()
    results: list[CropPriceWithCropOut] = []

    for crop in crops:
        base_price = float(crop.base_price)

        previous = (
            db.query(CropDailyPrice)
            .filter(CropDailyPrice.crop_id == crop.id, CropDailyPrice.price_date < today)
            .order_by(desc(CropDailyPrice.price_date))
            .first()
        )

        if previous:
            last_price = float(previous.price)
            last_trend = previous.trend
        else:
            last_price = base_price
            last_trend = PriceTrend.stable

        # ط²ط®ظ… ط§ظ„ط§طھط¬ط§ظ‡: ظ¦ظ¥ظھ ط§ط­طھظ…ط§ظ„ ط§ط³طھظ…ط±ط§ط± ط§طھط¬ط§ظ‡ ط§ظ„ط£ظ…ط³طŒ ظ£ظ¥ظھ ط§ط­طھظ…ط§ظ„ ط§ظ†ط¹ظƒط§ط³ظ‡ ط£ظˆ ط«ط¨ظˆطھظ‡
        if last_trend == PriceTrend.up:
            momentum_bias = (
                random.uniform(0.3, 2.0) if random.random() < 0.65 else random.uniform(-2.0, 0.3)
            )
        elif last_trend == PriceTrend.down:
            momentum_bias = (
                random.uniform(-2.0, -0.3) if random.random() < 0.65 else random.uniform(-0.3, 2.0)
            )
        else:
            momentum_bias = random.uniform(-1.5, 1.5)

        # ط§ظ†ط¬ط°ط§ط¨ طھط¯ط±ظٹط¬ظٹ ظ†ط­ظˆ ط§ظ„ط³ط¹ط± ط§ظ„ط£ط³ط§ط³ظٹ ط¥ط°ط§ ط§ظ†ط­ط±ظپ ط§ظ„ط³ط¹ط± ظƒط«ظٹط±ط§ظ‹ ط¹ظ†ظ‡ (ظٹظ…ظ†ط¹ ط§ظ„ط§ظ†ظپظ„ط§طھ)
        deviation_pct = (last_price - base_price) / base_price * 100
        reversion = -0.15 * deviation_pct

        daily_change_pct = round(momentum_bias + reversion + random.uniform(-0.8, 0.8), 2)
        daily_change_pct = max(-6.0, min(6.0, daily_change_pct))

        new_price_value = round(last_price * (1 + daily_change_pct / 100), 2)
        change_percent = round((new_price_value - base_price) / base_price * 100, 1)

        trend = PriceTrend.up if daily_change_pct > 0.3 else (
            PriceTrend.down if daily_change_pct < -0.3 else PriceTrend.stable
        )
        market_status = (
            MarketStatus.excellent
            if change_percent > 5
            else MarketStatus.caution if change_percent < -5 else MarketStatus.stable
        )

        existing = (
            db.query(CropDailyPrice)
            .filter(CropDailyPrice.crop_id == crop.id, CropDailyPrice.price_date == today)
            .first()
        )
        if existing:
            existing.price = new_price_value
            existing.change_percent = change_percent
            existing.trend = trend
            existing.high_price = round(new_price_value * 1.08, 2)
            existing.low_price = round(new_price_value * 0.93, 2)
            existing.status = market_status
            existing.source = "simulated"
            record = existing
        else:
            record = CropDailyPrice(
                crop_id=crop.id,
                price_date=today,
                price=new_price_value,
                change_percent=change_percent,
                trend=trend,
                high_price=round(new_price_value * 1.08, 2),
                low_price=round(new_price_value * 0.93, 2),
                status=market_status,
                source="simulated",
            )
            db.add(record)

        db.flush()
        results.append(_build_price_with_crop(record))

    db.commit()
    return results


@router.post(
    "/refresh",
    response_model=list[CropPriceWithCropOut],
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.agronomist))],
)
def refresh_prices(db: Session = Depends(get_db)):
    """
    طھط­ط¯ظٹط« ط¬ظ…ط§ط¹ظٹ ظٹط¯ظˆظٹ ظ„ط£ط³ط¹ط§ط± ط§ظ„ظٹظˆظ… (ظ…طھط§ط­ ظ„ظ„ط£ط¯ظ…ظ†/ط®ط¨ظٹط± ط§ظ„ط²ط±ط§ط¹ط© ظپظ‚ط·) â€” ظٹط³طھط®ط¯ظ… ظ†ظپط³
    ظ…ظ†ط·ظ‚ ط§ظ„ظ…ط­ط§ظƒط§ط© ط§ظ„ط°ظƒظٹط© ط§ظ„ظ…ط³طھط®ط¯ظ… طھظ„ظ‚ط§ط¦ظٹط§ظ‹ ظپظٹ ط§ظ„ظ…ظ‡ظ…ط© ط§ظ„ظ…ط¬ط¯ظˆظ„ط© ط§ظ„ظٹظˆظ…ظٹط©.
    """
    return run_daily_price_simulation(db)
