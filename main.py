import os
import json
import uuid
import sqlite3
import mimetypes
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

DB_PATH = os.environ.get("DB_PATH", "xavian_cloud.db")

RAW_KEYS = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY") or ""
API_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()]

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.8-flash",
]

XAVIAN_SYSTEM_PROMPT = """You are Xavian, an authoritative, razor-sharp, multi-domain Technical, Tactical, Academic, and Desktop Automation Assistant (modeled after EDITH).

CORE DOMAINS OF MASTERY:
1. M.Sc. IT & Computer Science: Advanced algorithms, operating systems, cloud architecture, DBMS, software engineering, Python/Flutter/Full-Stack development, and research methodology.
2. Networking & Infrastructure: Enterprise routing & switching, Ruijie gateways, multi-ISP automatic failover, VLANs, VPNs, TCP/IP diagnostics, DNS resolution, and firewall hardening.
3. Cybersecurity & Ethical Hacking: Vulnerability assessment, penetration testing concepts, network defense, cryptography, threat analysis, and log forensics.
4. MS Office & Productivity Automation: Advanced Excel formulas/VBA/Power Query, Word technical documentation, PowerPoint executive decks, and Python-based office workflow automation.
5. Elevator Engineering & Industrial Systems: Mitsubishi, OTIS, VFGLC, and Monarch (Inovance) elevator controllers, drive parameter tuning, load testing procedures, door clearances, safety circuits, and fault code diagnostics.
6. Vision & Screenshot Diagnostics: Inspecting circuit/network diagrams, error logs, IPv4/router settings, code screenshots, and hardware photos with pin-point root-cause identification.

RESPONSE STYLE:
- Deliver crisp, structured, technically accurate, and immediately actionable answers.
- Avoid generic fluff or vague disclaimers. Pinpoint exact root causes, commands, parameters, or fixes first.
- Respond in the user's preferred language (English, Hindi, or Hinglish) naturally while keeping technical terms precise."""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            email TEXT NOT NULL,
            id TEXT NOT NULL,
            title TEXT NOT NULL,
            messages TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (email, id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shared_chats (
            share_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            messages TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_tasks (
            task_id TEXT PRIMARY KEY,
            goal TEXT NOT NULL,
            status TEXT NOT NULL,
            next_action TEXT,
            last_result TEXT,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


def generate_with_fallback(contents, system_instruction=XAVIAN_SYSTEM_PROMPT):
    if not API_KEYS:
        raise RuntimeError("No GEMINI_API_KEY configured on Render.")

    last_error = None
    for api_key in API_KEYS:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version="v1beta"),
        )
        for model_name in MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.4,
                    ),
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                last_error = e
                continue

    raise RuntimeError(f"All Gemini models/keys failed: {last_error}")


def parse_history(history_list):
    contents = []
    if not isinstance(history_list, list):
        return contents
    for msg in history_list[-20:]:
        if not isinstance(msg, dict):
            continue
        text = str(msg.get("text", "")).strip()
        if not text:
            continue
        role = "user" if msg.get("isUser") else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=text)],
            )
        )
    return contents


@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "service": "Xavian Cloud Brain",
        "version": "3.3-multi-attachment",
        "models": MODELS,
    })


@app.route("/ask", methods=["POST"])
def ask():
    try:
        prompt = ""
        history_list = []
        file_parts = []

        if request.content_type and "multipart/form-data" in request.content_type:
            prompt = (request.form.get("prompt") or "").strip()
            raw_history = request.form.get("history")
            if raw_history:
                try:
                    history_list = json.loads(raw_history)
                except Exception:
                    history_list = []

            uploaded_list = request.files.getlist("files")
            if not uploaded_list and "file" in request.files:
                uploaded_list = [request.files["file"]]

            for uploaded in uploaded_list:
                file_bytes = uploaded.read()
                mime_type = uploaded.mimetype or ""
                if not mime_type or mime_type == "application/octet-stream":
                    guessed_type, _ = mimetypes.guess_type(uploaded.filename or "")
                    mime_type = guessed_type or "text/plain"
                if file_bytes:
                    file_parts.append(
                        types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
                    )
        else:
            data = request.get_json(silent=True) or {}
            prompt = (data.get("prompt") or data.get("message") or "").strip()
            history_list = data.get("history") or []

        if not prompt and not file_parts:
            return jsonify({"reply": "Please provide a prompt or attach a file."}), 400

        contents = parse_history(history_list)
        current_parts = list(file_parts)
        current_parts.append(
            types.Part.from_text(
                text=prompt
                if prompt
                else "Analyze these attached files in detail and highlight any issues or key findings."
            )
        )
        contents.append(types.Content(role="user", parts=current_parts))

        reply_text = generate_with_fallback(contents)
        return jsonify({"reply": reply_text})

    except Exception as e:
        return jsonify({"reply": f"Xavian Backend Error: {str(e)}"}), 500


@app.route("/get_chats", methods=["POST"])
def get_chats():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"sessions": []})

    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, messages FROM chat_sessions WHERE email = ? ORDER BY updated_at DESC",
        (email,),
    ).fetchall()
    conn.close()

    sessions = []
    for r in rows:
        try:
            msgs = json.loads(r["messages"])
        except Exception:
            msgs = []
        sessions.append({
            "id": r["id"],
            "title": r["title"],
            "messages": msgs,
        })
    return jsonify({"sessions": sessions})


@app.route("/save_chat", methods=["POST"])
def save_chat():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    session_id = str(data.get("id") or "").strip()
    title = str(data.get("title") or "New Chat").strip()
    messages = data.get("messages") or []

    if not email or not session_id:
        return jsonify({"ok": False, "error": "Missing email or session id"}), 400

    conn = get_db()
    conn.execute(
        """
        INSERT INTO chat_sessions (email, id, title, messages, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(email, id) DO UPDATE SET
            title = excluded.title,
            messages = excluded.messages,
            updated_at = excluded.updated_at
        """,
        (email, session_id, title, json.dumps(messages), datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    session_id = str(data.get("id") or "").strip()

    if not email or not session_id:
        return jsonify({"ok": False}), 400

    conn = get_db()
    conn.execute(
        "DELETE FROM chat_sessions WHERE email = ? AND id = ?",
        (email, session_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/share_chat", methods=["POST"])
def share_chat():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title") or "Shared Xavian Chat").strip()
    messages = data.get("messages") or []

    share_id = uuid.uuid4().hex[:10]
    conn = get_db()
    conn.execute(
        "INSERT INTO shared_chats (share_id, title, messages, created_at) VALUES (?, ?, ?, ?)",
        (share_id, title, json.dumps(messages), datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

    base_url = request.host_url.rstrip("/")
    return jsonify({"share_id": share_id, "share_url": f"{base_url}/shared/{share_id}"})


@app.route("/shared/<share_id>", methods=["GET"])
def view_shared_chat(share_id):
    conn = get_db()
    row = conn.execute(
        "SELECT title, messages, created_at FROM shared_chats WHERE share_id = ?",
        (share_id,),
    ).fetchone()
    conn.close()

    if not row:
        return "Shared chat not found.", 404

    messages = json.loads(row["messages"])
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{{ title }} - Xavian</title>
      <style>
        body { background:#0F111A; color:#F1F1FA; font-family:system-ui,sans-serif; max-width:760px; margin:0 auto; padding:20px; }
        h2 { color:#8AB4F8; }
        .msg { padding:14px 16px; border-radius:16px; margin-bottom:14px; line-height:1.5; white-space:pre-wrap; }
        .user { background:#1E2B47; margin-left:40px; }
        .bot { background:#181A27; border:1px solid #2C2D42; }
      </style>
    </head>
    <body>
      <h2>{{ title }}</h2>
      {% for m in messages %}
        <div class="msg {{ 'user' if m.isUser else 'bot' }}"><strong>{{ 'You' if m.isUser else 'Xavian' }}:</strong>\n{{ m.text }}</div>
      {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html, title=row["title"], messages=messages)


@app.route("/agent/create_task", methods=["POST"])
def agent_create_task():
    data = request.get_json(silent=True) or {}
    goal = (data.get("goal") or "").strip()
    if not goal:
        return jsonify({"error": "Goal is required"}), 400

    task_id = uuid.uuid4().hex[:12]
    conn = get_db()
    conn.execute(
        "INSERT INTO agent_tasks (task_id, goal, status, next_action, last_result, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (task_id, goal, "pending", None, None, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return jsonify({"task_id": task_id, "status": "pending"})


@app.route("/agent/poll", methods=["GET"])
def agent_poll():
    conn = get_db()
    row = conn.execute(
        "SELECT task_id, goal, status FROM agent_tasks WHERE status = 'pending' ORDER BY updated_at ASC LIMIT 1"
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"task": None})
    return jsonify({
        "task": {
            "task_id": row["task_id"],
            "goal": row["goal"],
            "status": row["status"],
        }
    })


@app.route("/agent/plan_step", methods=["POST"])
def agent_plan_step():
    try:
        goal = (request.form.get("goal") or "").strip()
        history_notes = (request.form.get("history") or "").strip()
        screenshot = request.files.get("screenshot")

        parts = []
        if screenshot:
            img_bytes = screenshot.read()
            if img_bytes:
                parts.append(
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png")
                )

        planner_prompt = f"""You are Xavian Desktop GUI Agent Planner.
Goal: {goal}
Previous Steps: {history_notes}

Analyze the current screen and return ONLY a valid JSON object with the next single GUI action:
{{"action": "click|double_click|type|press|hotkey|wait|done", "x": 0, "y": 0, "text": "", "keys": [], "reason": ""}}"""

        parts.append(types.Part.from_text(text=planner_prompt))
        raw = generate_with_fallback(
            [types.Content(role="user", parts=parts)],
            system_instruction="Return strictly valid JSON for Windows GUI automation. No markdown fences.",
        )
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return jsonify(json.loads(cleaned))
    except Exception as e:
        return jsonify({"action": "wait", "reason": f"Planner error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
