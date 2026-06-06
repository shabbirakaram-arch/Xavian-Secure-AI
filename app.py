import streamlit as st
import requests
import json

# 1. Page Configuration (Sleek Desktop & Mobile Layout)
st.set_page_config(
    page_title="Xavian Secure AI", 
    page_icon="🛡️", 
    layout="centered"
)

# 2. API Key Setup (Streamlit Secrets se uthayega)
# Agar aap testing kar rahe hain toh direct string daal sakte hain: GEMINI_API_KEY = "AIzaSy..."
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    st.error("API Key nahi mili! Kripya Streamlit Secrets mein GEMINI_API_KEY set karein.")
    st.stop()

# 3. TOP INTERFACE (Jaise image 1000101366.png mein tha)
st.markdown("## 🛡️ Xavian Secure AI")

# Voice Input Guide Instruction
st.markdown(
    "🎙️ **Voice Input Guide:** Apne mobile keyboard ke **mike (🎙️)** icon ko daba kar bolein."
)
st.write("---")

# 4. CHAT HISTORY MANAGEMENT (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Purani chat history ko screen par dikhana
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. GEMINI STYLE CHAT INPUT BOX (Bottom Fixed)
if user_input := st.chat_input("Xavian Secure AI se kuch bhi poochein..."):
    
    # User ka message screen par dikhayein
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # History mein save karein
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Assistant response block
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Direct HTTP POST Request (Bina kisi library ke jhanjhat ke)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [
                {
                    "parts": [{"text": user_input}]
                }
            ]
        }
        
        try:
            # API ko call karna
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            
            # Response se text nikalna
            if response.status_code == 200:
                full_response = response_data['candidates'][0]['content']['parts'][0]['text']
            else:
                full_response = f"API Error: {response_data.get('error', {}).get('message', 'Kuch galat hua')}"
                
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            full_response = f"Connection Error: {str(e)}"
            message_placeholder.markdown(full_response)
            
    # AI ka response history mein save karein
    st.session_state.messages.append({"role": "assistant", "content": full_response})
