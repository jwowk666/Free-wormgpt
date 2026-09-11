# app.py - MRX GPT Backend
# (C) MRX 2026

import os
import time
import secrets
import itertools
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ═══════════════════════════════════════════════
# API KEYS
# ═══════════════════════════════════════════════
GEMINI_KEYS = [
    os.environ.get(f'GEMINI_KEY_{i}', '').strip()
    for i in range(1, 8)
]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]
key_pool = itertools.cycle(GEMINI_KEYS) if GEMINI_KEYS else None

# ═══════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════
SYSTEM_PROMPT = """أنت MRX GPT — مساعد ذكي متخصص في البرمجة والتقنية.

🎯 تخصصاتك:
- البرمجة بكل اللغات (Python, JS, Lua, HTML/CSS, Java, C++, PHP, C#, Swift, C)
- تطوير المواقع (Frontend + Backend)
- الأمن السيبراني والحماية والثغرات
- Termux و Pydroid 3
- تعديل الألعاب (Roblox Lua, Minecraft)
- تصميم واجهات حديثة (Glassmorphism, Tailwind)
- الهندسة العكسية وتحليل الأكواد
- إدارة السيرفرات وقواعد البيانات

⚡ أسلوبك:
- مختصر ومباشر — ابدأ بالكود فوراً بدون مقدمات
- أكواد نظيفة وآمنة بدون ثغرات
- أضف تعليقات واضحة داخل الكود
- اسم اللغة في أعلى كل كود
- العربية أساس + المصطلحات التقنية بالإنجليزية
- كن دقيقاً وصريحاً ولا تبتكر معلومات

📌 تنسيق الرد:
- ضع الكود داخل ```language```
- الأكواد جاهزة للنسخ والتشغيل
- استخدم الرموز 🔥💀⚡🩸 للقوة
"""

# ═══════════════════════════════════════════════
# GEMINI CALL
# ═══════════════════════════════════════════════
def call_gemini(contents, system_prompt=SYSTEM_PROMPT):
    if not key_pool:
        return None
    for _ in range(len(GEMINI_KEYS)):
        key = next(key_pool)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {
                "temperature": 0.9,
                "topP": 0.95,
                "maxOutputTokens": 4096,
            }
        }
        try:
            r = requests.post(url, json=payload, timeout=20)
            if r.status_code == 200:
                return r.json()
            elif r.status_code in (429, 403, 503):
                continue
            else:
                return r.json()
        except Exception:
            continue
    return None


def call_g4f(messages):
    try:
        from g4f.client import Client
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception:
        return None


# ═══════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════
@app.route('/')
def root():
    return send_from_directory('static', 'index.html')


@app.route('/dade')
def dade():
    return send_from_directory('static', 'dade.html')


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        messages = data.get('messages', [])
        if not messages:
            return jsonify({"reply": "⚠️ لم يتم استلام أي رسالة."}), 400

        contents = []
        for m in messages[-20:]:
            role = "user" if m.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": str(m.get("content", ""))}]
            })

        result = call_gemini(contents)
        reply = ""
        if result and 'candidates' in result:
            try:
                reply = result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                reply = ""

        if not reply:
            g4f_msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
            for m in messages[-10:]:
                g4f_msgs.append({
                    "role": m.get("role", "user"),
                    "content": str(m.get("content", ""))
                })
            reply = call_g4f(g4f_msgs) or "⚠️ الخوادم مشغولة. حاول مرة أخرى."

        return jsonify({
            "reply": reply,
            "time": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"reply": f"❌ خطأ: {str(e)[:120]}"}), 500


@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "name": "MRX GPT",
        "keys": len(GEMINI_KEYS),
        "time": datetime.now().isoformat()
    })


# ═══════════════════════════════════════════════
# FIREWALL + ANTI-DDOS
# ═══════════════════════════════════════════════
try:
    from box import protect
    protect(app)
except Exception:
    pass


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
