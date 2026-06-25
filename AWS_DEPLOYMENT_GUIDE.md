# AWS ga joylash (Deployment) qo'llanmasi

Loyihangiz serverda ishlashi uchun barcha zaruriy tayyorgarliklar ko'rildi. Quyida AWS serveriga joylash uchun qadamlar keltirilgan.

## 1. Server Tayyorgarligi (EC2)
AWS EC2 instance (masalan, Ubuntu 22.04) ochganingizdan so'ng, quyidagi komponentlarni o'rnating:
- **Python 3.12+**
- **PostgreSQL** (yoki AWS RDS ishlating)
- **Redis** (Celery va Cache uchun)
- **Nginx** (Reverse proxy sifatida)

## 2. Loyihani sozlash
Serverga kodlarni yuklagandan so'ng (git orqali), quyidagi ishlarni bajaring:

```bash
# Virtual muhit yaratish
python3 -m venv .venv
source .venv/bin/activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt
```

## 3. Environment Variables (.env)
`.env.example` faylidan nusxa olib, `.env` yarating va undagi qiymatlarni serverga moslang:
- `DEBUG=False`
- `ALLOWED_HOSTS` ga serveringiz IP manzili yoki domeningizni yozing.
- `DATABASE_URL` ga PostgreSQL ulanish manzilingizni kiriting.

## 4. Statik fayllar va Ma'lumotlar bazasi
```bash
python manage.py collectstatic --noinput
python manage.py migrate
```

## 5. Gunicorn va Daphne (Ishga tushirish)
Loyihada ham HTTP, ham WebSocket (Channels) borligi sababli, serverni quyidagicha ishga tushirish tavsiya etiladi:

**HTTP uchun (Gunicorn):**
```bash
gunicorn --workers 3 --bind 0.0.0.0:8000 config.wsgi:application
```

**WebSocket uchun (Daphne):**
```bash
daphne -b 0.0.0.0 -p 8001 config.asgi:application
```

## Muhim o'zgarishlar (Men tomondan qilingan):
- **Xavfsizlik:** `ALLOWED_HOSTS` endi faqat `.env` da ko'rsatilgan manzillardan qabul qiladi. `DEBUG=False` holatida xavfsizlik kuchaytirilgan.
- **Argon2:** Parollarni hashing qilish uchun `argon2-cffi` kutubxonasi `requirements.txt` ga qo'shildi.
- **Static files:** `whitenoise` sozlangan, bu serverda statik fayllarni osonroq tarqatishga yordam beradi.

## Tavsiya:
Agar Docker ishlatmoqchi bo'lsangiz, loyihada `docker-compose.yml` fayli bor. Undagi `DEBUG: 1` ni `0` ga o'zgartirib va `runserver` o'rniga `gunicorn` ishlatsangiz, AWS da osonroq ishga tushirishingiz mumkin.
