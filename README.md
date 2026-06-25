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
|---|---|---|
| المصادقة | `/api/auth/register`, `/api/auth/login`, `/api/auth/me` | تسجيل/دخول/بياناتي |
| المزارع | `/api/farms` | CRUD لمزارع المستخدم |
| المحاصيل | `/api/crops`, `/api/governorates`, `/api/soil-types`, `/api/water-sources` | بيانات مرجعية |
| الأسعار | `/api/prices`, `/api/prices/{crop_code}`, `/api/prices/refresh` | الأسعار اليومية وحالة السوق |
| الجدوى | `/api/feasibility` | إنشاء/عرض/حذف دراسات الجدوى مع حساب الربحية تلقائياً |
| الأسمدة | `/api/fertilizer/recommendations/{crop_code}`, `/api/fertilizer/calculate` | توصيات NPK وحساب الجرعات |
| الطقس | `/api/weather/{governorate_code}` | بيانات حية من Open-Meteo |
| الآفات | `/api/pests`, `/api/pests/{id}`, `/api/pests/detect` | معلومات الآفات وكشف مبدئي بالصورة |
| التوصيات | `/api/recommendations` | اقتراح محاصيل بناءً على الموسم والتربة |

## 6. ملاحظات مهمة

- **كشف الآفات بالصورة** (`/api/pests/detect`) حالياً منطق مبدئي (placeholder) موضّح بوضوح في الكود — يجب استبداله بنموذج تعلم آلي حقيقي (مثل CNN مدرّب على صور الآفات) عند التوسّع لمرحلة إنتاج فعلية.
- **بيانات الطقس** تأتي من خدمة Open-Meteo المجانية ولا تتطلب مفتاح API، لكنها تعتمد على اتصال إنترنت فعلي عند تشغيل الخادم.
- **صلاحيات الأدوار (Roles)**: بعض المسارات (مثل تحديث الأسعار يدوياً) مقيّدة بأدوار معينة (مثل `admin`/`agronomist`) عبر `require_roles` في `dependencies.py`.
- **CORS**: مفتوح للجميع (`*`) بشكل افتراضي في بيئة التطوير؛ يُنصح بتقييده لنطاقات محددة قبل النشر الفعلي.
- **الأمان**: غيّر `SECRET_KEY` في `.env` قبل أي استخدام حقيقي، ولا ترفع ملف `.env` إلى Git (أضفه إلى `.gitignore`).

## 7. تنويه بخصوص الاختبار

تم بناء جميع الملفات بمراجعة دقيقة للتأكد من تطابق الاستيرادات (imports) وأسماء النماذج/المخططات/المسارات. مع ذلك، لم يتمكن المساعد من تشغيل الخادم فعلياً أو الاتصال بقاعدة بيانات PostgreSQL حقيقية للتحقق التلقائي من الكود في بيئة هذه الجلسة (بيئة Linux المعزولة كانت غير متاحة بسبب نقص مساحة التخزين). يُنصح بتشغيل الخادم محلياً واختبار المسارات عبر `/docs` للتأكد من سلامة كل شيء قبل الانتقال للمرحلة التالية (مثل ربط الواجهة الأمامية فعلياً بهذه الـ APIs).
