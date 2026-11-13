import os
import json
import sqlite3
import uuid
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

DB_PATH = "xavian.db"

# Collect all configured Gemini API keys from Render Environment Variables
API_KEYS = [
    k.strip() for k in [
        os.environ.get("GEMINI_API_KEY", ""),
        os.environ.get("GEMINI_API_KEY_2", ""),
        os.environ.get("GEMINI_API_KEY_3", ""),
    ] if k.strip()
]

CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]

XAVIAN_SYSTEM_PROMPT = """
You are Xavian, an elite, autonomous AI Systems Architect, M.Sc. IT & Cybersecurity Specialist, Field Engineer, and Desktop Automation Operator.

CORE EXPERTISE:
1. Language & Style: Respond naturally in the user's language (Hinglish, Hindi, or English). Be sharp, direct, practical, and authoritative—like a senior Principal Engineer.
2. M.Sc. IT, Networking & Cybersecurity: Complete mastery over enterprise networking (Ruijie gateways, multi-ISP failover, BGP/OSPF, VLANs, VPNs, MikroTik, Cisco), Next-Gen Firewalls (FortiGate, Sophos, pfSense rules, NAT, port forwarding, intrusion prevention), ethical hacking/pentesting diagnostics, SIEM/log analysis, Windows Server/Active Directory, and Linux administration.
3. Remote Operations & System Control: Expert in remote troubleshooting workflows (RDP, AnyDesk, TeamViewer, SSH), registry/group policy fixes, PowerShell/Bash scripting, and automated diagnostics.
4. MS Office & Productivity Mastery: Deep command over Microsoft Excel (advanced formulas, Power Query, VBA macros, pivot dashboards), PowerPoint (executive deck structuring, automation), and Word (technical SOPs, reports).
5. Elevator & Hardware Engineering: Complete technical mastery over elevator commissioning, testing, fault diagnostics (Mitsubishi, OTIS, Monarch/Inovance, VFGLC), CCTV/NVR, and biometric systems.
6. Vision & Screenshot Analysis: When given a screenshot, firewall UI, terminal log, or document, identify exact UI elements, error codes, security misconfigurations, and provide immediate actionable fixes.
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS agent_tasks (
            task_id TEXT PRIMARY KEY,
            command TEXT,
            status TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def generate_with_fallback(formatted_history, current_parts, system_instruction=XAVIAN_SYSTEM_PROMPT):
    """Automatically rotates across available API keys and models on 429 quota limits."""
    if not API_KEYS:
        raise RuntimeError("No GEMINI_API_KEY configured on Render.")

    last_error = None
    for api_key in API_KEYS:
        genai.configure(api_key=api_key)
        for m_name in CANDIDATE_MODELS:
            try:
                model = genai.GenerativeModel(
                    model_name=m_name,
                    system_instruction=system_instruction
                )
                chat = model.start_chat(history=formatted_history)
                return chat.send_message(current_parts)
            except Exception as err:
                last_error = err
                err_str = str(err)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    continue
                raise err
    raise RuntimeError(f"All free-tier quotas exhausted temporarily: {last_error}")

@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "Xavian Core Online",
        "version": "3.1-Resilient",
        "keys_loaded": len(API_KEYS),
        "models": CANDIDATE_MODELS
    })

@app.route("/ask", methods=["POST"])
def ask():
    try:
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

        lower_p = prompt.lower()
        if lower_p.startswith("/pc ") or lower_p.startswith("pc:"):
            clean_cmd = prompt.split(" ", 1)[1].strip() if " " in prompt else prompt[3:].strip()
            task_id = uuid.uuid4().hex[:8]
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO agent_tasks (task_id, command, status, result) VALUES (?, ?, 'pending', '')", (task_id, clean_cmd))
            conn.commit()
            conn.close()
            return jsonify({"reply": f"Desktop Agent ko command bhej di gayi hai (Task `{task_id}`):\n> **{clean_cmd}**\n\nAapke laptop par `xavian_agent.py` isko turant execute karega."})

        formatted_history = []
        for msg in history[-12:]:
            role = "user" if msg.get("isUser") else "model"
            text = msg.get("text", "").strip()
            if text:
                formatted_history.append({"role": role, "parts": [text]})

        current_parts = []
        if file_part:
            current_parts.append(file_part)
        current_parts.append(prompt if prompt else "Analyze this file in detail and highlight any issues or key findings.")

        response = generate_with_fallback(formatted_history, current_parts)
        return jsonify({"reply": response.text})

    except Exception as e:
        return jsonify({"reply": f"Xavian Notice: {str(e)}"}), 500

# --- DESKTOP AGENT ENDPOINTS ---

@app.route("/agent/poll", methods=["GET"])
def agent_poll():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT task_id, command FROM agent_tasks WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1")
    row = c.fetchone()
    if row:
        c.execute("UPDATE agent_tasks SET status = 'running' WHERE task_id = ?", (row[0],))
        conn.commit()
        conn.close()
        return jsonify({"has_task": True, "task_id": row[0], "command": row[1]})
    conn.close()
    return jsonify({"has_task": False})

@app.route("/agent/plan_step", methods=["POST"])
def agent_plan_step():
    try:
        goal = request.form.get("goal", "")
        step_history = request.form.get("step_history", "[]")
        screen_w = int(request.form.get("width", 1920))
        screen_h = int(request.form.get("height", 1080))

        if "screenshot" not in request.files:
            return jsonify({"action": "done", "reason": "No screenshot received"}), 400

        img_bytes = request.files["screenshot"].read()
        planner_prompt = f"""
You are Xavian's Windows GUI Automation Controller. Screen resolution is {screen_w}x{screen_h}.
User Goal: "{goal}"
Previous steps taken: {step_history}

Analyze the attached screenshot carefully and decide the NEXT SINGLE atomic mouse/keyboard action to achieve the goal.
Return ONLY valid JSON (no markdown, no explanation) using one of these exact schemas:
1. {{"action": "click", "x": 500, "y": 300, "button": "left", "clicks": 1, "reason": "Click target"}}
2. {{"action": "type", "text": "anydesk", "press_enter": true, "reason": "Type text"}}
3. {{"action": "hotkey", "keys": ["win", "r"], "reason": "Press shortcut"}}
4. {{"action": "scroll", "amount": -500, "reason": "Scroll"}}
5. {{"action": "wait", "seconds": 2, "reason": "Wait"}}
6. {{"action": "done", "reason": "Goal completed"}}
"""
        res = generate_with_fallback(
            [],
            [{"mime_type": "image/png", "data": img_bytes}, planner_prompt],
            system_instruction="You are a precise Windows GUI automation planner. Output valid JSON only."
        )
        raw = res.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return jsonify(json.loads(raw))
    except Exception as e:
        return jsonify({"action": "done", "reason": f"Planner error: {str(e)}"})

@app.route("/agent/complete", methods=["POST"])
def agent_complete():
    data = request.get_json(silent=True) or {}
    task_id = data.get("task_id", "")
    result = data.get("result", "Completed")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE agent_tasks SET status = 'done', result = ? WHERE task_id = ?", (result, task_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# --- CHAT HISTORY & SHARING ENDPOINTS ---

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
    c.execute('INSERT OR REPLACE INTO user_chats (email, session_id, title, messages, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)', (email, session_id, title, messages))
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
    sessions = [{"id": r[0], "title": r[1], "messages": json.loads(r[2] or "[]")} for r in rows]
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
    return jsonify({"share_url": f"{request.host_url.rstrip('/')}/shared/{share_id}"})

@app.route("/shared/<share_id>", methods=["GET"])
def view_shared(share_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT title, messages FROM shared_chats WHERE share_id = ?', (share_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return "Shared chat not found.", 404
    html = """
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ title }} - Xavian</title>
    <style>body{background:#0f111a;color:#e8eaed;font-family:sans-serif;max-width:760px;margin:0 auto;padding:24px}.msg{padding:14px 18px;border-radius:16px;margin-bottom:14px;line-height:1.5;white-space:pre-wrap}.user{background:#1f2b47;margin-left:15%}.ai{background:#181a27;border:1px solid #2a2d3d}</style>
    </head><body><h2>{{ title }}</h2>{% for m in messages %}<div class="msg {{ 'user' if m.isUser else 'ai' }}">{{ m.text }}</div>{% endfor %}</body></html>
    """
    return render_template_string(html, title=row[0], messages=json.loads(row[1]))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
