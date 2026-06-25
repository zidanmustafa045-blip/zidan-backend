---
title: zidan-backend
emoji: 🌱
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# AgriVision Ultra — Backend (FastAPI)

باك-إند كامل لمنصة AgriVision Ultra الزراعية، مبني بـ FastAPI و SQLAlchemy و PostgreSQL، ويغطي: المصادقة عبر JWT، إدارة المزارع، أسعار المحاصيل اليومية، دراسات الجدوى الاقتصادية، توصيات الأسمدة (NPK)، بيانات الطقس، والآفات.

## 1. هيكل المشروع

```
agrivision_backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # نقطة تشغيل التطبيق وربط الـ routers
│   ├── config.py            # الإعدادات (متغيرات البيئة)
│   ├── database.py          # الاتصال بقاعدة البيانات (SQLAlchemy engine/session)
│   ├── security.py          # تجزئة كلمات المرور + توليد/فك تشفير JWT
│   ├── dependencies.py      # get_current_user و require_roles
│   ├── models.py            # نماذج SQLAlchemy (الجداول)
│   ├── schemas.py            # مخططات Pydantic (الطلبات/الاستجابات)
│   └── routers/
│       ├── __init__.py
│       ├── auth.py           # /api/auth/* (تسجيل، دخول، بياناتي)
│       ├── farms.py          # /api/farms/*
│       ├── crops.py          # /api/crops، /api/governorates، إلخ
│       ├── prices.py         # /api/prices/*
│       ├── feasibility.py    # /api/feasibility/*
│       ├── fertilizer.py     # /api/fertilizer/*
│       ├── weather.py        # /api/weather/*
│       ├── pests.py          # /api/pests/*
│       └── recommendations.py # /api/recommendations
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```

## 2. المتطلبات الأساسية

- Python 3.11 أو أحدث.
- PostgreSQL 14 أو أحدث (يعمل محلياً على المنفذ الافتراضي 5432).
- (اختياري) `psql` لتشغيل ملف `agrivision_schema.sql` مباشرة.

## 3. خطوات التشغيل المحلي (Localhost)

### الخطوة 1: إنشاء بيئة افتراضية وتثبيت المتطلبات

```bash
cd agrivision_backend
python -m venv venv

# تفعيل البيئة الافتراضية:
# على Windows:
venv\Scripts\activate
# على macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### الخطوة 2: إنشاء قاعدة البيانات في PostgreSQL

```bash
# الدخول إلى psql وإنشاء قاعدة البيانات
psql -U postgres -c "CREATE DATABASE agrivision;"
```

### الخطوة 3: تجهيز الجداول — هناك طريقتان

**الطريقة أ — تشغيل ملف SQL الجاهز مباشرة (الأسرع):**

```bash
psql -U postgres -d agrivision -f ../agrivision_schema.sql
```

**الطريقة ب — استخدام Alembic (يولّد الجداول من نماذج SQLAlchemy في models.py):**

```bash
# توليد أول ترحيل تلقائياً بمقارنة النماذج بقاعدة بيانات فارغة
alembic revision --autogenerate -m "initial schema"

# تطبيق الترحيل على قاعدة البيانات
alembic upgrade head
```

> ملاحظة: إذا استخدمت الطريقة (أ) لإنشاء الجداول، يمكنك تجاهل Alembic في البداية، أو تشغيل `alembic stamp head` لإعلام Alembic أن قاعدة البيانات متوافقة مع آخر إصدار من النماذج دون إعادة تنفيذ شيء.

### الخطوة 4: ضبط متغيرات البيئة

```bash
cp .env.example .env
```

ثم عدّل ملف `.env` ليطابق بيئتك (خاصة `DATABASE_URL` إذا اختلفت بيانات اتصال PostgreSQL لديك، و `SECRET_KEY` لقيمة عشوائية قوية).

### الخطوة 5: تشغيل الخادم

```bash
uvicorn app.main:app --reload
```

سيعمل الخادم على: `http://localhost:8000`

### الخطوة 6: تجربة الـ API

- وثائق Swagger التفاعلية: `http://localhost:8000/docs`
- وثائق ReDoc: `http://localhost:8000/redoc`
- فحص الصحة: `http://localhost:8000/health`

## 4. تدفّق المصادقة (Authentication)

1. `POST /api/auth/register` — تسجيل حساب جديد (اسم، بريد إلكتروني، كلمة مرور، دور اختياري).
2. `POST /api/auth/login` — تسجيل الدخول (نموذج `username`/`password` بصيغة OAuth2 form-data)، يُعيد `access_token`.
3. أرسل التوكن في كل طلب محمي عبر الترويسة: `Authorization: Bearer <access_token>`.
4. `GET /api/auth/me` — لجلب بيانات المستخدم الحالي والتحقق من صلاحية التوكن.

في صفحة `/docs`، يمكنك الضغط على زر "Authorize" وإدخال التوكن لتجربة المسارات المحمية مباشرة من المتصفح.

## 5. أهم المسارات (Endpoints)

| المجموعة | المسار | الوصف |
|