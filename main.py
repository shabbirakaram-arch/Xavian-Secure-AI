import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)  # Isse cross-origin restrictions hat jayengi

# Gemini Client Initialize karein
# Render ke Environment Variables mein GEMINI_API_KEY add karna mat bhulna bhai
client = genai.Client()

# Route ko '/ask' kiya taaki HTML file ke fetch request se match ho sake
@app.route('/ask', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json()
        user_message = data.get('prompt', '')  # HTML se 'prompt' key aati hai

        if not user_message:
            return jsonify({'error': 'Message cannot be empty!'}), 400

        # Gemini AI ko System Instruction set karna
        config = types.GenerateContentConfig(
            system_instruction=(
                "You are Xavian Secure AI, an elite cyber security expert, network engineer, and digital forensics specialist. "
                "Provide professional, highly accurate, and secure coding or networking advice. "
                "Keep responses structured, clean, and concise."
            ),
            temperature=0.7,
        )

        # Gemini Model se response generate karwana
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=config
        )

        # HTML script 'answer' key expect karti hai
        return jsonify({'answer': response.text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
