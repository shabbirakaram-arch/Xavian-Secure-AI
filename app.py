import streamlit as st
from google import genai
import os

# 1. Page Configuration (Mobile & Desktop dono ke liye sleek look)
st.set_page_config(
    page_title="Xavian Secure AI", 
    page_icon="🛡️", 
    layout="centered"
)

# 2. Gemini API Client Setup
# Aapko apni Gemini API Key system environment me set karni hogi, ya phir yahan direct paste kar sakte hain.
# Secure tarika: os.environ.get("GEMINI_API_KEY")
# Testing ke liye aap direct string bhi daal sakte hain: client = genai.Client(api_key="APNI_API_KEY_YAHAN_LIKHO")
try:
    client = genai.Client()
except Exception as e:
    st.error("API Key nahi mili! Kripya apni Gemini API Key set karein.")
    st.stop()

# 3. TOP INTERFACE (Jaise aapki image 1000101366.png mein tha)
st.markdown("## 🛡️ Xavian Secure AI")

# Voice Input Guide Instruction
st.markdown(
    "🎙️ **Voice Input Guide:** Apne mobile keyboard ke **mike (🎙️)** icon ko daba kar bolein."
)
st.write("---")

# 4. CHAT HISTORY MANAGEMENT (Session State)
# Agar chat history pehle se nahi bani, toh initialize karein
if "messages" not in st.session_state:
    st.session_state.messages = []

# Pehle se maujood chat messages ko screen par render/display karna
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. GEMINI STYLE CHAT INPUT BOX (Bottom Fixed)
if user_input := st.chat_input("Xavian Secure AI se kuch bhi poochein..."):
    
    # User ka message screen par turant dikhayein
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Message ko history mein save karein
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Gemini AI se response generate karna
    with st.chat_message("assistant"):
        message_placeholder = st.empty() # Loading/Streaming effect ke liye placeholder
        full_response = ""
        
        try:
            # Gemini-2.5-flash model fast aur efficient chat ke liye best hai
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_input
            )
            full_response = response.text
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            full_response = f"Sorry, ek error aaya: {str(e)}"
            message_placeholder.markdown(full_response)
            
    # AI ka response bhi history mein save karein taaki screen refresh par gayab na ho
    st.session_state.messages.append({"role": "assistant", "content": full_response})
