import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)  # Isse Flutter app bina kisi restriction ke backend se connect ho payegi

# 1. Gemini Client Initialize karein
# Laptop par run karte waqt terminal mein apna API key set karein: export GEMINI_API_KEY="your_api_key"
client = genai.Client()

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json()
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        # 2. Gemini AI ko Cyber-Security Expert banane ke liye System Instruction set karna
        config = types.GenerateContentConfig(
            system_instruction=(
                "You are Xavian Secure AI, an elite cyber security expert, network engineer, and digital forensics specialist. "
                "Provide professional, highly accurate, and secure coding or networking advice. "
                "Keep responses structured, clean, and concise."
            ),
            temperature=0.7,
        )

        # 3. Gemini Model se response generate karwana
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=config,
        )

        return jsonify({'response': response.text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Cloud (Render) aur local execution dono ke liye port setup
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
