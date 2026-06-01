import os
import ssl
import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Network Fixes
ssl._create_default_https_context = ssl._create_unverified_context
os.environ["PYTHONHTTPSVERIFY"] = "0"

# Streamlit Page Config
st.set_page_config(page_title="Xavian Secure AI", page_icon="🛡️", layout="centered")

# --- COMPLETE GEMINI UI OVERHAUL (TRULY INTEGRATED + BUTTON) ---
st.markdown("""
    <style>
    /* ऐप बैकग्राउंड */
    .stApp {
        background-color: #131314;
        color: #e3e3e3;
        margin-bottom: 120px; /* ताकि चैट मैसेजेस इनपुट बार के पीछे न छुपें */
    }
    
    /* चैट मैसेज बबल्स */
    div[data-testid="stChatMessage"] {
        background-color: #1e1f20 !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
    }
    div[data-testid="stChatMessage"] p {
        color: #ffffff !important;
        font-size: 16px !important;
    }

    /* --- REAL GEMINI BOTTOM STICKY BAR --- */
    .gemini-footer-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #131314;
        padding: 20px 0 30px 0;
        z-index: 99999;
    }
    
    /* इनपुट बॉक्स और प्लस बटन को बांधने वाला असली कंटेनर */
    .gemini-input-container {
        max-width: 700px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        background-color: #1e1f20;
        border: 1px solid #444746;
        border-radius: 32px;
        padding: 6px 14px;
        position: relative;
    }

    /* 1. प्लस बटन (File Uploader Customization) */
    .upload-zone {
        position: relative;
        width: 36px;
        height: 36px;
        min-width: 36px;
        margin-right: 10px;
    }
    div[data-testid="stFileUploader"] {
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        z-index: 10;
        opacity: 0; /* असली ड्रैग-एंड-ड्रॉप को छुपा दिया */
    }
    /* नकली प्लस डिजाइन जो यूजर को दिखेगा */
    .fake-plus-btn {
        width: 36px;
        height: 36px;
        background-color: #2b2c2e;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #e3e3e3;
        font-size: 24px;
        font-weight: bold;
        pointer-events: none; /* क्लिक असली उप्लोअदेर पर ही होगा */
    }

    /* 2. टेक्स्ट इनपुट (चैट बॉक्स) */
    div[data-testid="stTextInput"] {
        flex-grow: 1;
    }
    div[data-testid="stTextInput"] > div > div > input {
        background-color: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 16px !important;
        padding: 0 !important;
        box-shadow: none !important;
    }
    /* डिफ़ॉल्ट लेबल को गायब करना */
    div[data-testid="stTextInput"] label {
        display: none !important;
    }

    /* 3. सेंड बटन */
    .send-zone {
        margin-left: 10px;
    }
    .send-zone button {
        background-color: #1a73e8 !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        font-size: 16px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* प्रिव्यू थंबनेल */
    .preview-box {
        max-width: 700px;
        margin: -15px auto 10px auto;
        padding: 0 10px;
    }

    /* डिफ़ॉल्ट चीजें छिपाएं */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Xavian Secure AI")

# Secure Config Setup
if "GEMINI_SECRET_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_SECRET_KEY"]
    os.environ["GEMINI_SECRET_KEY"] = api_key
    genai.configure(api_key=api_key)
else:
    api_key = None

if not api_key:
    st.error("❌ Error: Streamlit Secrets में API Key गायब है!")
else:
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 1. चैट हिस्ट्री रेंडर करना
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message and message["image"] is not None:
                st.image(message["image"], use_container_width=True)

    # 2. सिलेक्टेड फोटो का प्रिव्यू दिखाना (इनपुट बार के ठीक ऊपर)
    preview_container = st.container()

    # Voice Guide
    st.markdown("<br><br>🎙️ **Voice Input Guide:** अपने मोबाइल कीबोर्ड के माइक (🎙️) से बोलें।", unsafe_allow_html=True)

    # --- 3. कस्टमाइज्ड जेमिनी बॉटम बार कंटेनर ---
    st.markdown('<div class="gemini-footer-bar">', unsafe_allow_html=True)
    st.markdown('<div class="gemini-input-container">', unsafe_allow_html=True)
    
    # [A] प्लस बटन जोन
    st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("uploader", type=["jpg", "jpeg", "png"], label_visibility="collapsed", key="gemini_upload")
    st.markdown('<div class="fake-plus-btn">+</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # [B] टेक्स्ट इनपुट जोन
    # यहाँ हमने st.chat_input की जगह st.text_input का इस्तेमाल किया है
    user_prompt = st.text_input("prompt_input", placeholder="Xavian Secure AI से कुछ भी पूछें...", label_visibility="collapsed", key="user_text")
    
    # [C] सेंड बटन जोन
    st.markdown('<div class="send-zone">', unsafe_allow_html=True)
    submit_clicked = st.button("➔", key="send_btn")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True) # input container बंद
    st.markdown('</div>', unsafe_allow_html=True) # footer bar बंद

    # प्रिव्यू लॉजिक
    if uploaded_file:
        with preview_container:
            st.markdown('<div class="preview-box">', unsafe_allow_html=True)
            img_preview = Image.open(uploaded_file)
            st.image(img_preview, caption="📎 तैयार है", width=80)
            st.markdown('</div>', unsafe_allow_html=True)

    # 4. सबमिट होने पर चैट प्रोसेसिंग (यूजर या तो एंटर दबाए या सेंड बटन पर क्लिक करे)
    if (user_prompt and submit_clicked) or (user_prompt and st.session_state.user_text != ""):
        # डुप्लीकेट ट्रिगर रोकने के लिए चेक
        if "last_processed" not in st.session_state or st.session_state.last_processed != user_prompt:
            st.session_state.last_processed = user_prompt
            
            user_msg = {"role": "user", "content": user_prompt, "image": None}
            input_image = None
            
            if uploaded_file:
                input_image = Image.open(uploaded_file)
                user_msg["image"] = input_image
            
            st.session_state.messages.append(user_msg)
            
            # असिस्टेंट रिस्पांस
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🤖 *Xavian सोच रहा है...*")
                
                try:
                    if input_image:
                        response = model.generate_content([user_prompt, input_image])
                    else:
                        response = model.generate_content(user_prompt)
                        
                    ai_response = response.text
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    error_msg = f"❌ एरर: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
            # इनपुट साफ़ करने और यूआई रीलोड करने के लिए
            st.rerun()
            
