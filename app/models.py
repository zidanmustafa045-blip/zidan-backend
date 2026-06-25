"""
نماذج SQLAlchemy (ORM Models) — مطابقة لمخطط قاعدة البيانات agrivision_schema.sql
"""

import enum
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


# ============================================================================
# ENUMS (تطابق ENUM types في PostgreSQL)
# ============================================================================
class UserRole(str, enum.Enum):
    admin = "admin"
    agronomist = "agronomist"
    farmer = "farmer"
    viewer = "viewer"


class CropSeason(str, enum.Enum):
    winter = "winter"
    summer = "summer"
    nili = "nili"
    year = "year"


class CostItemType(str, enum.Enum):
    fixed = "fixed"
    variable = "variable"


class PestSeverity(str, enum.Enum):
    low = "منخفض"
    medium = "متوسط"
    high = "عالي"


class PriceTrend(str, enum.Enum):
    up = "up"
    down = "down"
    stable = "stable"


class MarketStatus(str, enum.Enum):
    excellent = "ممتاز"
    stable = "مستقر"
    caution = "حذر"


class FeasibilityStatus(str, enum.Enum):
    draft = "draft"
    completed = "completed"
    archived = "archived"


class ReportFormat(str, enum.Enum):
    pdf = "pdf"
    excel = "excel"


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


# ============================================================================
# LOOKUP TABLES
# ============================================================================
class Governorate(Base):
    __tablename__ = "governorates"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True)
    name_ar = Column(String(60), nullable=False)
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="governorate")
    farms = relationship("Farm", back_populates="governorate")


class SoilType(Base):
    __tablename__ = "soil_types"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True)
    name_ar = Column(String(40), nullable=False)


class WaterSource(Base):
    __tablename__ = "water_sources"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True)
    name_ar = Column(String(40), nullable=False)


# ============================================================================
# USERS & FARMS
# ============================================================================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(120), nullable=False)
    email = Column(String(160), nullable=False, unique=True, index=True)
    phone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.farmer)
    governorate_id = Column(SmallInteger, ForeignKey("governorates.id", ondelete="SET NULL"))
    avatar_url = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True)
    email_verified_at = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    governorate = relationship("Governorate", back_populates="users")
    farms = relationship("Farm", back_populates="owner", cascade="all, delete-orphan")
    feasibility_studies = relationship("FeasibilityStudy", back_populates="user", cascade="all, delete-orphan")


class Farm(Base):
    __tablename__ = "farms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(120), nullable=False)
    governorate_id = Column(SmallInteger, ForeignKey("governorates.id", ondelete="SET NULL"))
    soil_type_id = Column(SmallInteger, ForeignKey("soil_types.id", ondelete="SET NULL"))
    water_source_id = Column(SmallInteger, ForeignKey("water_sources.id", ondelete="SET NULL"))
    area_feddan = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (CheckConstraint("area_feddan > 0", name="ck_farms_area_positive"),)

    owner = relationship("User", back_populates="farms")
    governorate = relationship("Governorate", back_populates="farms")
    soil_type = relationship("SoilType")
    water_source = relationship("WaterSource")


# ============================================================================
# CROPS & PRICES
# ============================================================================
class Crop(Base):
    __tablename__ = "crops"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(30), nullable=False, unique=True)
    name_ar = Column(String(60), nullable=False)
    emoji = Column(String(10))
    season = Column(Enum(CropSeason, name="crop_season"), nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    avg_yield_ton_feddan = Column(Numeric(10, 2), nullable=False)
    avg_cost_feddan = Column(Numeric(12, 2), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    prices = relationship("CropDailyPrice", back_populates="crop", cascade="all, delete-orphan")
    fertilizer_recommendation = relationship(
        "FertilizerRecommendation", back_populates="crop", uselist=False, cascade="all, delete-orphan"
    )


class CropDailyPrice(Base):
    __tablename__ = "crop_daily_prices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    crop_id = Column(SmallInteger, ForeignKey("crops.id", ondelete="CASCADE"), nullable=False)
    price_date = Column(Date, nullable=False, server_default=func.current_date())
    price = Column(Numeric(10, 2), nullable=False)
    change_percent = Column(Numeric(6, 2), nullable=False, default=0)
    trend = Column(Enum(PriceTrend, name="price_trend"), nullable=False, default=PriceTrend.stable)
    high_price = Column(Numeric(10, 2))
    low_price = Column(Numeric(10, 2))
    status = Column(Enum(MarketStatus, name="market_status", values_callable=lambda x: [e.value for e in x]), nullable=False, default=MarketStatus.stable)
    source = Column(String(60), default="system")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("crop_id", "price_date", name="uq_crop_price_date"),)

    crop = relationship("Crop", back_populates="prices")


# ============================================================================
# PESTS
# ============================================================================
class Pest(Base):
    __tablename__ = "pests"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    name_ar = Column(String(80), nullable=False)
    icon = Column(String(10))
    severity = Column(Enum(PestSeverity, name="pest_severity"), nullable=False)
    symptoms = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PestDetection(Base):
    __tablename__ = "pest_detections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id", ondelete="SET NULL"))
    crop_id = Column(SmallInteger, ForeignKey("crops.id", ondelete="SET NULL"))
    pest_id = Column(SmallInteger, ForeignKey("pests.id", ondelete="SET NULL"))
    image_url = Column(String(255), nullable=False)
    confidence = Column(Numeric(5, 2))
    detected_at = Column(DateTime(timezone=True), server_default=func.now())

    pest = relationship("Pest")
    crop = relationship("Crop")


# ============================================================================
# FERTILIZERS
# ============================================================================
class FertilizerRecommendation(Base):
    __tablename__ = "fertilizer_recommendations"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    crop_id = Column(SmallInteger, ForeignKey("crops.id", ondelete="CASCADE"), nullable=False, unique=True)
    fertilizer_type = Column(String(120), nullable=False)
    amount_per_feddan = Column(String(40), nullable=False)
    timing = Column(String(160), nullable=False)
    n_value = Column(SmallInteger, nullable=False)
    p_value = Column(SmallInteger, nullable=False)
    k_value = Column(SmallInteger, nullable=False)

    crop = relationship("Crop", back_populates="fertilizer_recommendation")


class FertilizerCalculation(Base):
    __tablename__ = "fertilizer_calculations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(SmallInteger, ForeignKey("crops.id", ondelete="CASCADE"), nullable=False)
    crop_age_days = Column(SmallInteger, nullable=False)
    leaf_color = Column(String(20), nullable=False)
    soil_type_id = Column(SmallInteger, ForeignKey("soil_types.id", ondelete="SET NULL"))
    recommended_n = Column(SmallInteger)
    recommended_p = Column(SmallInteger)
    recommended_k = Column(SmallInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================================================
# FEASIBILITY STUDIES
# ============================================================================
class FeasibilityStudy(Base):
    __tablename__ = "feasibility_studies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(SmallInteger, ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False)
    governorate_id = Column(SmallInteger, ForeignKey("governorates.id", ondelete="SET NULL"))
    soil_type_id = Column(SmallInteger, ForeignKey("soil_types.id", ondelete="SET NULL"))
    water_source_id = Column(SmallInteger, ForeignKey("water_sources.id", ondelete="SET NULL"))
    season = Column(Enum(CropSeason, name="crop_season"), nullable=False)
    area_feddan = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(FeasibilityStatus, name="feasibility_status"), nullable=False, default=FeasibilityStatus.draft)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="feasibility_studies")
    crop = relationship("Crop")
    cost_items = relationship("FeasibilityCostItem", back_populates="study", cascade="all, delete-orphan")
    result = relationship("FeasibilityResult", back_populates="study", uselist=False, cascade="all, delete-orphan")


class FeasibilityCostItem(Base):
    __tablename__ = "feasibility_cost_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    study_id = Column(UUID(as_uuid=True), ForeignKey("feasibility_studies.id", ondelete="CASCADE"), nullable=False)
    cost_type = Column(Enum(CostItemType, name="cost_item_type"), nullable=False)
    category = Column(String(60), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)

    study = relationship("FeasibilityStudy", back_populates="cost_items")


class FeasibilityResult(Base):
    __tablename__ = "feasibility_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    study_id = Column(
        UUID(as_uuid=True), ForeignKey("feasibility_studies.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    total_fixed_cost = Column(Numeric(14, 2), nullable=False, default=0)
    total_variable_cost = Column(Numeric(14, 2), nullable=False, default=0)
    total_cost = Column(Numeric(14, 2), nullable=False, default=0)
    cost_per_feddan = Column(Numeric(14, 2), nullable=False, default=0)
    expected_production_kg = Column(Numeric(14, 2), nullable=False, default=0)
    expected_revenue = Column(Numeric(14, 2), nullable=False, default=0)
    net_profit = Column(Numeric(14, 2), nullable=False, default=0)
    roi_percent = Column(Numeric(6, 2), nullable=False, default=0)
    payback_months = Column(Numeric(6, 1))
    is_profitable = Column(Boolean, nullable=False, default=False)
    ai_recommendation = Column(Text)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    study = relationship("FeasibilityStudy", back_populates="result")


# ============================================================================
# WEATHER
# ============================================================================
class WeatherLog(Base):
    __tablename__ = "weather_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    governorate_id = Column(SmallInteger, ForeignKey("governorates.id", ondelete="SET NULL"))
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    temperature = Column(Numeric(5, 2))
    humidity = Column(Numeric(5, 2))
    rainfall_mm = Column(Numeric(6, 2))
    wind_speed = Column(Numeric(5, 2))
    condition_text = Column(String(60))

    governorate = relationship("Governorate")


# ============================================================================
# CROP RECOMMENDATION ENGINE (NPK)
# ============================================================================
class CropRecommendation(Base):
    __tablename__ = "crop_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    nitrogen = Column(SmallInteger, nullable=False)
    phosphorus = Column(SmallInteger, nullable=False)
    potassium = Column(SmallInteger, nullable=False)
    temperature = Column(Numeric(5, 2), nullable=False)
    humidity = Column(Numeric(5, 2), nullable=False)
    rainfall_mm = Column(Numeric(6, 2), nullable=False)
    recommended_crop_id = Column(SmallInteger, ForeignKey("crops.id", ondelete="SET NULL"))
    confidence = Column(Numeric(5, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recommended_crop = relationship("Crop")


# ============================================================================
# ALERTS & REPORTS
# ============================================================================
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(SmallInteger, ForeignKey("crops.id", ondelete="SET NULL"))
    severity = Column(Enum(AlertSeverity, name="alert_severity"), nullable=False, default=AlertSeverity.info)
    message = Column(String(255), nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(160), nullable=False)
    format = Column(Enum(ReportFormat, name="report_format"), nullable=False)
    file_path = Column(String(255))
    generated_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================================================
# ADS (عروض/إعلانات الشركات) — تُقدَّم من الشركات وتتم مراجعتها من الأدمن
# ============================================================================
class Ad(Base):
    __tablename__ = "ads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(160), nullable=False)
    contact_name = Column(String(120))
    contact_email = Column(String(160), nullable=False)
    contact_phone = Column(String(20))
    title = Column(String(160), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    admin_note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
