import os
import ssl
import streamlit as st
import google.generativeai as genai

# 1. Pydroid 3 Network Setup & Fixes
ssl._create_default_https_context = ssl._create_unverified_context
os.environ["PYTHONHTTPSVERIFY"] = "0"

# 2. Secure Environment Configuration
# Kripya apni NAYI API Key yahan niche quotes (" ") ke andar dalein:
os.environ["GEMINI_SECRET_KEY"] = st.secrets["GEMINI_SECRET_KEY"]
# Streamlit Page Setup (Responsive for Mobile/Laptop)
st.set_page_config(page_title="Xavian Secure AI", page_icon="🛡️", layout="centered")
st.title("🛡️ Xavian Secure AI")
st.caption("A Secure & Powerful Web Assistant powered by Gemini 1.5")

# Fetch key from environment
api_key = os.environ.get("GEMINI_SECRET_KEY")

if not api_key or api_key == "PASTE_YOUR_NEW_API_KEY_HERE":
    st.error("❌ Error: Kripya pehle code me apni asli NAYI API Key dalein!")
else:
    # Gemini Setup
    genai.configure(api_key=api_key)
    
    # Initialize Chat History in Session
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Old Chat Messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input Box
    if prompt := st.chat_input("Xavian Secure AI se kuch bhi poohein..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate Response using Client config
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤖 *Xavian soch raha hai...*")
            
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                full_response = response.text
                message_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"❌ System Error: {str(e)}"
                message_placeholder.markdown(full_response)
                
        st.session_state.messages.append({"role": "assistant", "content": full_response})
