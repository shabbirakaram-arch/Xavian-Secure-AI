import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI(title="Xavian Secure AI Backend")

# Render par deploy karne ke baad yeh key environment variable se uthayega
API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_ACTUAL_GEMINI_API_KEY_HERE")

if API_KEY and API_KEY != "YOUR_ACTUAL_GEMINI_API_KEY_HERE":
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

class ChatRequest(BaseModel):
    prompt: str

@app.get("/")
def home():
    return {"status": "online", "message": "Xavian Secure Core Shield Active"}

@app.post("/ask")
def ask_xavian(request: ChatRequest):
    global model
    if not model:
        raise HTTPException(status_code=500, detail="Gemini Engine not configured on Server.")
    
    try:
        ai_res = model.generate_content(request.prompt)
        return {"answer": ai_res.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Routing Error: {str(e)}")
