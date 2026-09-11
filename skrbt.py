# skrbt.py - Email Verification System
# (C) MRX 2026

import os
import time
import random
import string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, jsonify, request

app = Flask(__name__)

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")

CODES = {}


def gen_code():
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(6))


def build_html(code):
    boxes = "".join(
        f'<div style="display:inline-block;width:52px;height:68px;'
        f'background:#1a0000;border:1.5px solid #ff0055;border-radius:10px;'
        f'margin:0 5px;font-family:monospace;font-size:34px;color:#ff4466;'
        f'font-weight:bold;text-align:center;line-height:68px;'
        f'box-shadow:0 0 15px rgba(255,0,85,.5);">{c}</div>'
        for c in code
    )
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"></head>
<body style="background:#000;margin:0;padding:40px 0;font-family:'Segoe UI',sans-serif;">
  <div style="max-width:520px;margin:0 auto;background:#000;border:1px solid #ff0055;
              border-radius:18px;padding:50px 30px;text-align:center;
              box-shadow:0 0 60px rgba(255,0,85,.3);">
    <h2 style="color:#fff;font-size:26px;margin:0 0 10px;text-shadow:0 0 8px #ff0055;">
      MRX GPT — رمز التحقق
    </h2>
    <p style="color:#bbb;font-size:15px;margin:0 0 35px;">
      استخدم الرمز أدناه للتحقق. صالح لمدة 10 دقائق.
    </p>
    <div style="margin-bottom:35px;">{boxes}</div>
    <p style="color:#666;font-size:13px;border-top:1px solid #222;padding-top:20px;margin:0;">
      إذا لم تطلب الرمز، تجاهل الرسالة.
    </p>
  </div>
</body>
</html>"""


@app.route('/send-code', methods=['POST'])
def send_code():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()
    if not email or '@' not in email:
        return jsonify({"status": "error", "message": "بريد غير صالح"}), 400

    code = gen_code()
    CODES[email] = {"code": code, "time": time.time()}

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return jsonify({
            "status": "success",
            "message": "تم التوليد (وضع محلي)",
            "debug_code": code
        })

    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = "MRX GPT — رمز التحقق"
        msg.attach(MIMEText(build_html(code), 'html'))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as s:
            s.starttls()
            s.login(SENDER_EMAIL, SENDER_PASSWORD)
            s.sendmail(SENDER_EMAIL, email, msg.as_string())

        return jsonify({"status": "success", "message": "تم الإرسال"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"فشل: {str(e)[:80]}"}), 500


@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()
    code = (data.get('code') or '').strip().upper()

    entry = CODES.get(email)
    if not entry:
        return jsonify({"status": "error", "message": "لم يتم إرسال رمز"}), 400
    if time.time() - entry["time"] > 600:
        del CODES[email]
        return jsonify({"status": "error", "message": "انتهت الصلاحية"}), 400
    if entry["code"] == code:
        del CODES[email]
        return jsonify({"status": "success", "message": "تم التحقق"})
    return jsonify({"status": "error", "message": "الرمز خطأ"}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
