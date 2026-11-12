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
        user_message = ""
        uploaded_file = None

        # Check karein ki request Multipart (File + Text) hai ya normal JSON
        if request.content_type and "multipart/form-data" in request.content_type:
            user_message = request.form.get("prompt", "").strip()
            uploaded_file = request.files.get("file")
        else:
            data = request.get_json(silent=True)
            if data:
                user_message = data.get("prompt", "").strip()

        if not user_message and not uploaded_file:
            return jsonify({
                "error": "Please enter a message or attach a file."
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
If the user attaches an image, document, or PDF, analyze it thoroughly and explain clearly.

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
        # Contents (File + Text dono support karne ke liye)
        # --------------------------------------------------

        contents = []

        if uploaded_file:
            file_bytes = uploaded_file.read()
            mime_type = uploaded_file.mimetype or "application/octet-stream"
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

        # --------------------------------------------------
        # Gemini request
        # --------------------------------------------------

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
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
