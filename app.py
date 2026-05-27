import os
import ssl
import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Network Fixes
ssl._create_default_https_context = ssl._create_unverified_context
os.environ["PYTHONHTTPSVERIFY"] = "0"

# 2. Secure Config
os.environ["GEMINI_SECRET_KEY"] = st.secrets["GEMINI_SECRET_KEY"]

# Streamlit Page Config
st.set_page_config(page_title="Xavian Secure AI", page_icon="🛡️", layout="centered")

# --- PRO GEMINI-STYLE UI CSS ---
st.markdown("""
    <style>
    /* पूरे ऐप का बैकग्राउंड और फॉन्ट */
    .stApp {
        background-color: #131314;
        color: #e3e3e3;
    }
    
    /* चैट इनपुट कंटेनर को जेमिनी जैसा राउंड और बैकग्राउंड देना */
    div[data-testid="stChatInput"] {
        border: 1px solid #444746 !important;
        border-radius: 32px !important;
        background-color: #1e1f20 !important;
        padding-left: 10px !important;
        padding-right: 10px !important;
    }
    
    /* इनपुट टेक्स्ट एरिया */
    div[data-testid="stChatInput"] textarea {
        color: #e3e3e3 !important;
    }
    
    /* सेंड बटन को ब्लू और गोल करना */
    button[data-testid="stChatInputSubmitButton"] {
        background-color: #1a73e8 !important;
        color: white !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
    }
    
    /* अपलोड बटन्स का बड़ा बॉक्स छोटा और छिपाना (ताकि सिर्फ आइकॉन जैसा लगे) */
    .css-1544g2n, .stFileUploader {
        padding-top: 0px !important;
        margin-bottom: 0px !important;
    }
    
    /* कस्टम जेमिनी फ्लोटिंग बार सेटअप */
    .gemini-bar-container {
        background: #1e1f20;
        border: 1px solid #444746;
        border-radius: 28px;
        padding: 10px 15px;
        margin-bottom: 15px;
    }
    
    .gemini-title {
        color: #8ab4f8;
        font-weight: bold;
        font-size: 14px;
        margin-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Xavian Secure AI")
st.caption("Google Gemini संचालित सुरक्षित वेब असिस्टेंट")

api_key = os.environ.get("GEMINI_SECRET_KEY")

if not api_key:
    st.error("❌ Error: Streamlit Secrets में API Key गायब है!")
else:
    genai.configure(api_key=api_key)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # चैट हिस्ट्री दिखाना
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message:
                st.image(message["image"], use_container_width=True)

    # --- GEMINI INPUT TOOLBAR (नीचे चैट बार के ठीक ऊपर) ---
    st.markdown('<div class="gemini-bar-container"><div class="gemini-title">✨ Gemini Smart Tools (+ 📸 🎙️)</div>', unsafe_allow_html=True)
    
    # 3 कॉलम्स में टूल्स को व्यवस्थित करना
    col1, col2, col3 = st.columns([1, 1, 1])
    
    uploaded_file = None
    
    with col1:
        # प्लस आइकॉन और गैलरी/फाइल के लिए
        doc_file = st.file_uploader("➕ Files/Gallery", type=["jpg", "jpeg", "png", "pdf", "txt"], key="gemini_plus")
    with col2:
        # कैमरा/लेंस आइकॉन के लिए
        img_file = st.file_uploader("📸 Lens/Camera", type=["jpg", "jpeg", "png"], key="gemini_lens")
    with col3:
        # वॉइस असिस्टेंस के लिए गाइडेंस
        voice_on = st.checkbox("🎙️ Mic Mode")
        if voice_on:
            st.info("💡 अपने कीबोर्ड का 🎙️ दबाकर बोलें!")
            
    st.markdown('</div>', unsafe_allow_html=True)

    # मीडिया हैंडलिंग
    if img_file:
        uploaded_file = img_file
    elif doc_file:
        uploaded_file = doc_file

    if uploaded_file and uploaded_file.type.startswith("image/"):
        preview_img = Image.open(uploaded_file)
        st.image(preview_img, caption="📎 सिलेक्टेड फोटो भेजने के लिए तैयार है", width=120)

    # मुख्य इनपुट बॉक्स
    if prompt := st.chat_input("Xavian Secure AI से कुछ भी पूछें..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        
        user_msg = {"role": "user", "content": prompt}
        if uploaded_file and uploaded_file.type.startswith("image/"):
            user_msg["image"] = Image.open(uploaded_file)
            
        st.session_state.messages.append(user_msg)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤖 *Xavian सोच रहा है...*")
            
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                if uploaded_file and uploaded_file.type.startswith("image/"):
                    img_data = Image.open(uploaded_file)
                    response = model.generate_content([prompt, img_data])
                else:
                    response = model.generate_content(prompt)
                    
                full_response = response.text
                message_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"❌ सिस्टम एरर: {str(e)}"
                message_placeholder.markdown(full_response)
                
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()
        
