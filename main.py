import json
import mimetypes
import os
import sqlite3
import uuid
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not configured")

client = genai.Client(
    api_key=api_key,
    http_options={'api_version': 'v1beta'}
)

DB_PATH = os.environ.get("DB_PATH", "xavian_data.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_email TEXT NOT NULL,
            title TEXT NOT NULL,
            messages_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shared_chats (
            share_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            messages_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


init_db()


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "Xavian AI Backend",
        "message": "AI backend with cloud sync & sharing is running."
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


# --------------------------------------------------
# Save & Fetch Cloud Chat History (By User Email)
# --------------------------------------------------

@app.route("/save_chat", methods=["POST"])
def save_chat():
    data = request.get_json(silent=True) or {}
    user_email = (data.get("email") or "").strip().lower()
    session_id = (data.get("id") or "").strip()
    title = (data.get("title") or "New Chat").strip()
    messages = data.get("messages") or []

    if not user_email or not session_id:
        return jsonify({"error": "email and session id required"}), 400

    conn = get_db()
    conn.execute("""
        INSERT INTO chat_sessions (session_id, user_email, title, messages_json, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(session_id) DO UPDATE SET
            title = excluded.title,
            messages_json = excluded.messages_json,
            updated_at = CURRENT_TIMESTAMP
    """, (session_id, user_email, title, json.dumps(messages)))
    conn.commit()
    conn.close()

    return jsonify({"status": "saved"})


@app.route("/get_chats", methods=["POST"])
def get_chats():
    data = request.get_json(silent=True) or {}
    user_email = (data.get("email") or "").strip().lower()
    if not user_email:
        return jsonify({"sessions": []})

    conn = get_db()
    rows = conn.execute("""
        SELECT session_id, title, messages_json
        FROM chat_sessions
        WHERE user_email = ?
        ORDER BY updated_at DESC
    """, (user_email,)).fetchall()
    conn.close()

    sessions = []
    for r in rows:
        sessions.append({
            "id": r["session_id"],
            "title": r["title"],
            "messages": json.loads(r["messages_json"])
        })

    return jsonify({"sessions": sessions})


@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    data = request.get_json(silent=True) or {}
    user_email = (data.get("email") or "").strip().lower()
    session_id = (data.get("id") or "").strip()

    conn = get_db()
    conn.execute(
        "DELETE FROM chat_sessions WHERE session_id = ? AND user_email = ?",
        (session_id, user_email)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


# --------------------------------------------------
# Shareable Conversation Link
# --------------------------------------------------

@app.route("/share_chat", methods=["POST"])
def share_chat():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "Shared Conversation").strip()
    messages = data.get("messages") or []

    if not messages:
        return jsonify({"error": "Cannot share empty chat"}), 400

    share_id = uuid.uuid4().hex[:10]
    conn = get_db()
    conn.execute(
        "INSERT INTO shared_chats (share_id, title, messages_json) VALUES (?, ?, ?)",
        (share_id, title, json.dumps(messages))
    )
    conn.commit()
    conn.close()

    share_url = f"{request.host_url.rstrip('/')}/shared/{share_id}"
    return jsonify({"share_url": share_url, "share_id": share_id})


@app.route("/shared/<share_id>", methods=["GET"])
def view_shared_chat(share_id):
    conn = get_db()
    row = conn.execute(
        "SELECT title, messages_json FROM shared_chats WHERE share_id = ?",
        (share_id,)
    ).fetchone()
    conn.close()

    if not row:
        return "<h2>Shared chat not found or expired.</h2>", 404

    messages = json.loads(row["messages_json"])
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{{ title }} - Xavian AI</title>
        <style>
            body { background: #0f111a; color: #f1f1fa; font-family: system-ui, sans-serif; margin: 0; padding: 20px; }
            .container { max-width: 720px; margin: auto; }
            .header { border-bottom: 1px solid #26293a; padding-bottom: 14px; margin-bottom: 20px; }
            .badge { color: #8ab4f8; font-size: 13px; font-weight: 600; }
            .msg { margin-bottom: 18px; padding: 14px 18px; border-radius: 18px; line-height: 1.55; white-space: pre-wrap; }
            .user { background: #1e2b47; margin-left: 40px; }
            .ai { background: #181a27; border: 1px solid #26293a; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="badge">✨ Xavian Shared Conversation</div>
                <h2>{{ title }}</h2>
            </div>
            {% for m in messages %}
                <div class="msg {{ 'user' if m.isUser else 'ai' }}">
                    <strong>{{ 'You' if m.isUser else 'Xavian' }}:</strong><br>{{ m.text }}
                </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, title=row["title"], messages=messages)


# --------------------------------------------------
# AI Chat (/ask)
# --------------------------------------------------

@app.route("/ask", methods=["POST"])
def ask():
    try:
        user_message = ""
        uploaded_file = None

        if request.content_type and "multipart/form-data" in request.content_type:
            user_message = request.form.get("prompt", "").strip()
            uploaded_file = request.files.get("file")
        else:
            data = request.get_json(silent=True)
            if data:
                user_message = data.get("prompt", "").strip()

        if not user_message and not uploaded_file:
            return jsonify({"error": "Please enter a message or attach a file."}), 400

        system_instruction = """
You are a helpful personal AI assistant.
Give accurate, practical, and easy-to-understand answers.
If the user attaches an image, document, or PDF, analyze it thoroughly and explain clearly.
Be friendly, professional, and concise.
"""

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=2048,
        )

        contents = []

        if uploaded_file:
            file_bytes = uploaded_file.read()
            mime_type = uploaded_file.mimetype
            if not mime_type or mime_type == "application/octet-stream":
                guessed_type, _ = mimetypes.guess_type(uploaded_file.filename or "")
                mime_type = guessed_type or "image/jpeg"

            contents.append(
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type,
                )
            )

        if user_message:
            contents.append(user_message)
        elif uploaded_file:
            contents.append("Please analyze this file and explain its key details clearly.")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config
        )

        answer = response.text
        if not answer:
            return jsonify({"error": "Gemini returned an empty response."}), 500

        return jsonify({"answer": answer})

    except Exception as e:
        print("Gemini Error:", repr(e))
        return jsonify({"error": "AI request failed.", "details": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
