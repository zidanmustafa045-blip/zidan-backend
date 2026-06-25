"""
Pydantic Schemas — نماذج التحقق من بيانات الطلبات (Request) والاستجابات (Response)
"""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import (
    CostItemType,
    CropSeason,
    FeasibilityStatus,
    MarketStatus,
    PestSeverity,
    PriceTrend,
    UserRole,
)


# ============================================================================
# AUTH / USERS
# ============================================================================
class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    phone: Optional[str] = None
    governorate_id: Optional[int] = None
    # NOTE: 'role' intentionally removed from public registration schema.
    # Public users can never self-assign a role (fixes privilege-escalation vuln).
    # Roles other than 'farmer' may only be granted by an admin via /api/admin routes.


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole
    governorate_id: Optional[int] = None
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenPayload(BaseModel):
    sub: str
    exp: int


# ============================================================================
# FARMS
# ============================================================================
class FarmCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    governorate_id: Optional[int] = None
    soil_type_id: Optional[int] = None
    water_source_id: Optional[int] = None
    area_feddan: float = Field(..., gt=0)


class FarmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    governorate_id: Optional[int] = None
    soil_type_id: Optional[int] = None
    water_source_id: Optional[int] = None
    area_feddan: float
    created_at: datetime


# ============================================================================
# LOOKUPS
# ============================================================================
class GovernorateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_ar: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SoilTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_ar: str


class WaterSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_ar: str


# ============================================================================
# CROPS
# ============================================================================
class CropOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_ar: str
    emoji: Optional[str] = None
    season: CropSeason
    base_price: float
    avg_yield_ton_feddan: float
    avg_cost_feddan: float
    description: Optional[str] = None
    is_active: bool


# ============================================================================
# PRICES
# ============================================================================
class CropPriceCreate(BaseModel):
    crop_code: str
    price: float = Field(..., ge=0)
    change_percent: float = 0
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    price_date: Optional[date] = None


class CropPriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    crop_id: int
    price_date: date
    price: float
    change_percent: float
    trend: PriceTrend
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    status: MarketStatus


class CropPriceWithCropOut(CropPriceOut):
    crop_code: str
    crop_name_ar: str
    crop_emoji: Optional[str] = None


# ============================================================================
# FEASIBILITY
# ============================================================================
class FeasibilityCostItemIn(BaseModel):
    cost_type: CostItemType
    category: str = Field(..., max_length=60)
    amount: float = Field(..., ge=0)


class FeasibilityCostItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cost_type: CostItemType
    category: str
    amount: float


class FeasibilityCreate(BaseModel):
    crop_code: str
    governorate_id: Optional[int] = None
    soil_type_id: Optional[int] = None
    water_source_id: Optional[int] = None
    season: CropSeason
    area_feddan: float = Field(..., gt=0)
    cost_items: list[FeasibilityCostItemIn] = Field(default_factory=list)


class FeasibilityResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_fixed_cost: float
    total_variable_cost: float
    total_cost: float
    cost_per_feddan: float
    expected_production_kg: float
    expected_revenue: float
    net_profit: float
    roi_percent: float
    payback_months: Optional[float] = None
    is_profitable: bool
    ai_recommendation: Optional[str] = None
    calculated_at: datetime


class FeasibilityStudyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    crop_id: int
    governorate_id: Optional[int] = None
    soil_type_id: Optional[int] = None
    water_source_id: Optional[int] = None
    season: CropSeason
    area_feddan: float
    status: FeasibilityStatus
    created_at: datetime
    cost_items: list[FeasibilityCostItemOut] = []
    result: Optional[FeasibilityResultOut] = None


# ============================================================================
# FERTILIZER
# ============================================================================
class FertilizerRecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crop_id: int
    fertilizer_type: str
    amount_per_feddan: str
    timing: str
    n_value: int
    p_value: int
    k_value: int


class FertilizerCalculateIn(BaseModel):
    crop_code: str
    crop_age_days: int = Field(..., ge=1, le=365)
    leaf_color: str = Field(..., pattern="^(green|yellow|brown|purple|spotted)$")
    soil_type_id: Optional[int] = None


class FertilizerCalculateOut(BaseModel):
    crop_code: str
    fertilizer_type: str
    amount_per_feddan: str
    timing: str
    recommended_n: int
    recommended_p: int
    recommended_k: int
    notes: str


# ============================================================================
# WEATHER
# ============================================================================
class WeatherCurrentOut(BaseModel):
    governorate_code: str
    governorate_name_ar: str
    temperature: float
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    condition_text: str
    recorded_at: datetime


class WeatherForecastDayOut(BaseModel):
    date: date
    max_temp: float
    min_temp: float
    rainfall_mm: float


class WeatherOut(BaseModel):
    current: WeatherCurrentOut
    forecast: list[WeatherForecastDayOut]


# ============================================================================
# PESTS
# ============================================================================
class PestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name_ar: str
    icon: Optional[str] = None
    severity: PestSeverity
    symptoms: str
    solution: str


class PestDetectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    crop_id: Optional[int] = None
    pest_id: Optional[int] = None
    image_url: str
    confidence: Optional[float] = None
    detected_at: datetime
    pest: Optional[PestOut] = None


# ============================================================================
# CROP RECOMMENDATION (NPK)
# ============================================================================
class CropRecommendationIn(BaseModel):
    nitrogen: int = Field(..., ge=0, le=140)
    phosphorus: int = Field(..., ge=0, le=145)
    potassium: int = Field(..., ge=0, le=205)
    temperature: float = Field(..., ge=5, le=50)
    humidity: float = Field(..., ge=10, le=100)
    rainfall_mm: float = Field(..., ge=0, le=500)


class CropRecommendationOut(BaseModel):
    recommended_crop_code: Optional[str] = None
    recommended_crop_name_ar: Optional[str] = None
    confidence: float
    explanation: str


# ============================================================================
# ADMIN / إدارة المستخدمين
# ============================================================================
class UserUpdateByAdmin(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class AdminStatsOut(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    users_by_role: dict[str, int]
    total_ads: int
    pending_ads: int


# ============================================================================
# ADS (عروض الشركات)
# ============================================================================
class AdCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=160)
    contact_name: Optional[str] = None
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    title: str = Field(..., min_length=2, max_length=160)
    message: str = Field(..., min_length=5)


class AdOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str
    contact_name: Optional[str] = None
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    title: str
    message: str
    status: str
    admin_note: Optional[str] = None
    created_at: datetime


class AdUpdateByAdmin(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|approved|rejected)$")
    admin_note: Optional[str] = None
