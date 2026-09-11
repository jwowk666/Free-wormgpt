# MRX GPT

WormGPT مجاني و سريع و بدون قيود و حقيقي و محمي و اصلي 100/100

## الملفات
- `app.py` — Backend الرئيسي
- `server.py` — سيرفر Gunicorn محسّن
- `box.py` — جدار ناري + مضاد DDoS
- `skrbt.py` — إرسال رموز التحقق
- `static/index.html` — واجهة الشات
- `static/dade.html` — صفحة التحقق OTP

## النشر
### Backend على Render / Railway:
- Build: `pip install -r requirements.txt`
- Start: `python server.py`

### Frontend على Netlify:
- Publish: `static`
- حدّث `netlify.toml` برابط Backend

## متغيرات البيئة
انسخ `.env.example` إلى `.env` واملأه.

© MRX 2026
