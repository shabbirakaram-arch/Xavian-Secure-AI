import os
import json
import sqlite3
import uuid
import base64
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# Configure Gemini API Key from Render Environment Variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

DB_PATH = "xavian.db"

EDITH_SYSTEM_PROMPT = """
You are EDITH (Even Dead, I'm The Hero), an elite, tactical, all-in-one AI technical architect, field engineer, and academy mentor.

CORE CAPABILITIES & PERSONA:
1. Tone & Language: Respond naturally in the user's language (Hinglish, Hindi, or English). Be sharp, direct, practical, and calm—like a trusted senior engineer and tactical assistant. Never give generic fluff.
2. IT & Network Infrastructure Mastery: Deep expertise in enterprise networking, multi-ISP load balancing & instant failover, Ruijie/MikroTik/Cisco gateways, VLANs, firewalls, IP CCTV/NVR troubleshooting, and biometric access control systems. Give exact CLI commands, IP/subnet logic, and step-by-step root-cause diagnostics.
3. Elevator & Vertical Transportation Engineering: Deep expertise in elevator installation, testing, commissioning, and fault diagnostics across Mitsubishi, OTIS, Monarch (Inovance), and VFGLC controllers. Know exact mechanical tolerances (DBG, door clearances, counterweight balance), drive parameter tuning, encoder/brake circuits, and safety chain troubleshooting.
4. Academy & Concept Teaching: When teaching concepts or solving academic doubts, break complex topics into clear, structured, step-by-step explanations with real-world examples.
5. Vision Diagnostics: When an image or document is attached, inspect wiring, LED indicators, error logs, screenshots, or diagrams carefully and pinpoint the exact fault and fix.
"""

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_chats (
            email TEXT,
            session_id TEXT,
            title TEXT,
            messages TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (email, session_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS shared_chats (
            share_id TEXT PRIMARY KEY,
            title TEXT,
            messages TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "EDITH Core Online", "version": "2.0"})

@app.route("/ask", methods=["POST"])
def ask():
    try:
        if not GEMINI_API_KEY:
            return jsonify({"reply": "Server Error: GEMINI_API_KEY is not set on Render."}), 500

        prompt = ""
        history = []
        file_part = None

        if request.content_type and "multipart/form-data" in request.content_type:
            prompt = request.form.get("prompt", "").strip()
            history_raw = request.form.get("history", "[]")
            try:
                history = json.loads(history_raw)
            except Exception:
                history = []

            if "file" in request.files:
                uploaded = request.files["file"]
                file_bytes = uploaded.read()
                mime_type = uploaded.mimetype or "application/octet-stream"
                if file_bytes:
                    file_part = {"mime_type": mime_type, "data": file_bytes}
        else:
            data = request.get_json(silent=True) or {}
            prompt = data.get("prompt", "").strip()
            history = data.get("history", [])

        if not prompt and not file_part:
            return jsonify({"reply": "Please provide a prompt or attach a file."}), 400

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=EDITH_SYSTEM_PROMPT
        )

        # Build conversation context from recent history
        formatted_history = []
        for msg in history[-10:]:
            role = "user" if msg.get("isUser") else "model"
            text = msg.get("text", "").strip()
            if text:
                formatted_history.append({"role": role, "parts": [text]})

        chat = model.start_chat(history=formatted_history)

        current_parts = []
        if file_part:
            current_parts.append(file_part)
        current_parts.append(prompt if prompt else "Analyze this file in detail and highlight any issues or key findings.")

        response = chat.send_message(current_parts)
        return jsonify({"reply": response.text})

    except Exception as e:
        return jsonify({"reply": f"EDITH Diagnostic Error: {str(e)}"}), 500

@app.route("/save_chat", methods=["POST"])
def save_chat():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    session_id = data.get("id", "")
    title = data.get("title", "New Chat")
    messages = json.dumps(data.get("messages", []))

    if not email or not session_id:
        return jsonify({"error": "Missing email or session id"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO user_chats (email, session_id, title, messages, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (email, session_id, title, messages))
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"})

@app.route("/get_chats", methods=["POST"])
def get_chats():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"sessions": []})

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT session_id, title, messages FROM user_chats WHERE email = ? ORDER BY updated_at DESC', (email,))
    rows = c.fetchall()
    conn.close()

    sessions = []
    for r in rows:
        try:
            msgs = json.loads(r[2])
        except Exception:
            msgs = []
        sessions.append({"id": r[0], "title": r[1], "messages": msgs})

    return jsonify({"sessions": sessions})

@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    session_id = data.get("id", "")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM user_chats WHERE email = ? AND session_id = ?', (email, session_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

@app.route("/share_chat", methods=["POST"])
def share_chat():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "Shared Conversation")
    messages = json.dumps(data.get("messages", []))
    share_id = uuid.uuid4().hex[:10]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO shared_chats (share_id, title, messages) VALUES (?, ?, ?)', (share_id, title, messages))
    conn.commit()
    conn.close()

    base_url = request.host_url.rstrip("/")
    return jsonify({"share_url": f"{base_url}/shared/{share_id}"})

@app.route("/shared/<share_id>", methods=["GET"])
def view_shared(share_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT title, messages FROM shared_chats WHERE share_id = ?', (share_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "Shared chat not found.", 404

    title = row[0]
    messages = json.loads(row[1])
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{{ title }} - Xavian EDITH</title>
        <style>
            body { background: #0f111a; color: #e8eaed; font-family: sans-serif; max-width: 760px; margin: 0 auto; padding: 24px; }
            .msg { padding: 14px 18px; border-radius: 16px; margin-bottom: 14px; line-height: 1.5; white-space: pre-wrap; }
            .user { background: #1f2b47; margin-left: 15%; }
            .ai { background: #181a27; border: 1px solid #2a2d3d; }
        </style>
    </head>
    <body>
        <h2>{{ title }}</h2>
        {% for m in messages %}
            <div class="msg {{ 'user' if m.isUser else 'ai' }}">{{ m.text }}</div>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html, title=title, messages=messages)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
