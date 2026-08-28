import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

# --------------------------------------------------
# Gemini API
# API key Render Environment Variable se aayegi
# Variable name: GEMINI_API_KEY
# --------------------------------------------------

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not configured")

client = genai.Client(api_key=api_key)


# --------------------------------------------------
# Home / Health Check
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "Xavian AI Backend",
        "message": "AI backend is running successfully."
    })


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    })


# --------------------------------------------------
# AI Chat
# --------------------------------------------------

@app.route("/ask", methods=["POST"])
def ask():

    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "error": "Request body is missing."
            }), 400

        user_message = data.get("prompt", "").strip()

        if not user_message:
            return jsonify({
                "error": "Please enter a message."
            }), 400

        # --------------------------------------------------
        # Assistant personality
        # --------------------------------------------------

        system_instruction = """
You are a helpful personal AI assistant.

Your job is to help the user with:
- General questions
- Education
- Technology
- Computers
- Networking
- Cybersecurity
- Coding
- Business ideas
- Writing
- Research
- Productivity

Give accurate, practical and easy-to-understand answers.

Do not pretend to have performed an action if you have not actually performed it.

For cybersecurity requests, remain within legal and authorized use.

Be friendly, professional and concise.
"""

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=2048,
        )

        # --------------------------------------------------
        # Gemini request
        # --------------------------------------------------

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=config
        )

        answer = response.text

        if not answer:
            return jsonify({
                "error": "Gemini returned an empty response."
            }), 500

        return jsonify({
            "answer": answer
        })

    except Exception as e:

        print("Gemini Error:", repr(e))

        return jsonify({
            "error": "AI request failed.",
            "details": str(e)
        }), 500


# --------------------------------------------------
# Render server
# --------------------------------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
