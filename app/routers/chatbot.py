"""
راوتر الشات بوت الذكي: يجاوب على أسئلة المستخدمين بالاستعلام المباشر من قاعدة
البيانات الحقيقية (الأسعار، الأسمدة، الآفات، بيانات المحاصيل)، بدلاً من ردود
عشوائية ثابتة كما كان في الواجهة سابقاً.
"""

import re
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Crop, CropDailyPrice, FertilizerRecommendation, Pest

router = APIRouter(prefix="/api/chatbot", tags=["الشات بوت الذكي - Chatbot"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    intent: str


PRICE_KEYWORDS = ["سعر", "اسعار", "أسعار", "ثمن", "بكام", "تسعير"]
FERTILIZER_KEYWORDS = ["سماد", "اسمدة", "أسمدة", "تسميد"]
PEST_KEYWORDS = ["آفة", "افة", "حشرة", "مرض", "آفات", "افات"]
GREETING_KEYWORDS = ["مرحبا", "السلام", "اهلا", "أهلا", "هاي", "hello", "hi"]


def _find_crop(db: Session, message: str) -> Crop | None:
    crops = db.query(Crop).filter(Crop.is_active.is_(True)).all()
    for crop in crops:
        if crop.name_ar and crop.name_ar in message:
            return crop
        if crop.code and crop.code.lower() in message.lower():
            return crop
    return None


def _any_keyword(message: str, keywords: list[str]) -> bool:
    return any(k in message for k in keywords)


@router.post("/ask", response_model=ChatResponse)
def ask_chatbot(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    يحلّل رسالة المستخدم، يحدّد القصد (سعر / سماد / آفة / معلومة عامة عن
    محصول)، ثم يبني رداً مبنياً على بيانات حقيقية من قاعدة البيانات.
    """
    message = (payload.message or "").strip()
    if not message:
        return ChatResponse(reply="من فضلك اكتب سؤالك حتى أقدر أساعدك 🌱", intent="empty")

    crop = _find_crop(db, message)

    if _any_keyword(message, GREETING_KEYWORDS) and not crop:
        return ChatResponse(
            reply=(
                "أهلاً بيك في مساعد AgriVision 🤖 تقدر تسألني عن: "
                "سعر محصول معيّن، توصية السماد المناسبة له، أو الآفات الشائعة. "
                "مثال: «سعر القمح النهاردة» أو «سماد الذرة»."
            ),
            intent="greeting",
        )

    if crop and _any_keyword(message, PRICE_KEYWORDS):
        latest = (
            db.query(CropDailyPrice)
            .filter(CropDailyPrice.crop_id == crop.id)
            .order_by(desc(CropDailyPrice.price_date))
            .first()
        )
        if not latest:
            return ChatResponse(
                reply=f"للأسف لا يوجد سعر مسجّل لمحصول {crop.name_ar} حالياً.",
                intent="price_not_found",
            )
        trend_ar = {"up": "في ارتفاع 📈", "down": "في انخفاض 📉", "stable": "مستقر ➖"}.get(
            latest.trend.value if hasattr(latest.trend, "value") else str(latest.trend), "مستقر"
        )
        reply = (
            f"{crop.emoji or ''} سعر {crop.name_ar} بتاريخ {latest.price_date}: "
            f"{float(latest.price):.0f} جنيه، والسعر {trend_ar} "
            f"({float(latest.change_percent):+.1f}%)."
        )
        return ChatResponse(reply=reply, intent="price")

    if crop and _any_keyword(message, FERTILIZER_KEYWORDS):
        rec = (
            db.query(FertilizerRecommendation)
            .filter(FertilizerRecommendation.crop_id == crop.id)
            .first()
        )
        if not rec:
            return ChatResponse(
                reply=f"لا توجد توصية سماد مسجّلة لمحصول {crop.name_ar} حالياً.",
                intent="fertilizer_not_found",
            )
        reply = (
            f"التوصية القياسية لسماد {crop.name_ar}: نوع السماد {rec.fertilizer_type}، "
            f"بمعدّل {rec.amount_per_feddan} للفدان، التوقيت المناسب: {rec.timing}. "
            f"(NPK: {rec.n_value}-{rec.p_value}-{rec.k_value})"
        )
        return ChatResponse(reply=reply, intent="fertilizer")

    if _any_keyword(message, PEST_KEYWORDS):
        pests = db.query(Pest).order_by(Pest.name_ar).limit(3).all()
        if not pests:
            return ChatResponse(reply="لا توجد بيانات آفات مسجّلة حالياً.", intent="pest_not_found")
        names = "، ".join(f"{p.icon or ''} {p.name_ar} ({p.severity})" for p in pests)
        return ChatResponse(
            reply=f"من أشهر الآفات المسجّلة في قاعدة البيانات حالياً: {names}. "
            "اسألني عن اسم آفة محدّدة لمعرفة الأعراض والحل.",
            intent="pest_list",
        )

    if crop:
        season_ar = {
            "winter": "شتوي",
            "summer": "صيفي",
            "nili": "نيلي",
            "year": "على مدار السنة",
        }.get(crop.season.value if hasattr(crop.season, "value") else str(crop.season), "")
        reply = (
            f"{crop.emoji or ''} محصول {crop.name_ar}: موسم الزراعة {season_ar}، "
            f"متوسط الإنتاجية {crop.avg_yield_ton_feddan} طن/فدان، "
            f"متوسط التكلفة {crop.avg_cost_feddan} جنيه/فدان. "
            f"{crop.description or ''}"
        ).strip()
        return ChatResponse(reply=reply, intent="crop_info")

    return ChatResponse(
        reply=(
            "لم أفهم سؤالك تماماً 🤔 جرّب تسأل عن سعر محصول معيّن (مثل: سعر القمح)، "
            "أو توصية سماد محصول، أو الآفات الشائعة."
        ),
        intent="fallback",
    )
