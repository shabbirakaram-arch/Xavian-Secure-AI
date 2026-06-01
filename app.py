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

# --- COMPLETE FIXED GEMINI BAR UI ---
st.markdown("""
    <style>
    /* पूरे ऐप का बैकग्राउंड */
    .stApp {
        background-color: #131314;
        color: #e3e3e3;
    }
    
    h1 {
        font-size: max(1.8rem, 4vw) !important;
    }
    
    /* चैट मैसेजेस */
    div[data-testid="stChatMessage"] {
        background-color: #1e1f20 !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
    }
    div[data-testid="stChatMessage"] p {
        color: #ffffff !important;
        font-size: 16px !important;
    }

    /* --- BOTTOM FIXED CONTAINER (Binds Everything Together Seamlessly) --- */
    .gemini-sticky-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #131314;
        padding: 15px 10px 25px 10px;
        z-index: 99999;
        box-shadow: 0 -10px 20px #131314;
    }
    
    .gemini-inner-bar {
        max-width: 700px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        background-color: #1e1f20;
        border: 1px solid #444746;
        border-radius: 28px;
        padding: 4px 10px;
    }

    /* 1. Plus Button Wrapper */
    .plus-wrapper {
        width: 36px;
        height: 36px;
        min-width: 36px;
        position: relative;
        margin-right: 8px;
    }
    /* Streamlit Uploader Styling to match a simple '+' */
    div[data-testid="stFileUploader"] {
        width: 100% !important;
    }
    div[data-testid="stFileUploader"] section {
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
    }
    div[data-testid="stFileUploader"] section > input + div {
        display: none !important;
    }
    div[data-testid="stFileUploader"] button {
        background-color: #2b2c2e !important;
        color: #e3e3e3 !important;
        border: none !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        min-width: 36px !important;
        font-size: 20px !important;
        font-weight: bold !important;
        padding: 0 !important;
    }
    div[data-testid="stFileUploader"] button::before {
        content: "+" !important;
    }
    div[data-testid="stFileUploader"] button span {
        display: none !important;
    }

    /* 2. Text Input Field */
    .input-wrapper {
        flex-grow: 1;
    }
    div[data-testid="stTextInput"] > div > div > input {
        background-color: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 16px !important;
        padding: 6px 0 !important;
        box-shadow: none !important;
    }

    /* 3. Send Button */
    .send-wrapper button {
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
        margin-left: 5px;
    }

    /* Floating Image Preview */
    .fixed-preview-box {
        max-width: 700px;
        margin: 0 auto 8px auto;
        padding: 0 10px;
    }

    /* Hide standard UI blocks */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stTextInput"] label {display: none !important;}
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

    # 1. Chat History Render
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message and message["image"] is not None:
                st.image(message["image"], use_container_width=True)

    # Space filler so chat history doesn't hide behind footer bar
    st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)

    # 2. FIXED STICKY CONTAINER (HTML + Streamlit Widgets Hybrid)
    st.markdown('<div class="gemini-sticky-footer">', unsafe_allow_html=True)
    
    # [A] Image Preview (If file is selected, shows right above the input bar)
    preview_placeholder = st.empty()
    
    # [B] Inside the rounded input container
    st.markdown('<div class="gemini-inner-bar">', unsafe_allow_html=True)
    
    # Column 1: Plus Button
    st.markdown('<div class="plus-wrapper">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed", key="stable_plus_btn")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Column 2: Text Input Field
    st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)
    user_prompt = st.text_input("", placeholder="Xavian Secure AI से कुछ भी पूछें...", label_visibility="collapsed", key="stable_text_input")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Column 3: Send Arrow Button
    st.markdown('<div class="send-wrapper">', unsafe_allow_html=True)
    submit_clicked = st.button("➔", key="stable_send_btn")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True) # Inner bar close
    st.markdown('</div>', unsafe_allow_html=True) # Sticky footer close

    # Show preview if file exists
    if uploaded_file:
        with preview_placeholder.container():
            st.markdown('<div class="fixed-preview-box">', unsafe_allow_html=True)
            img_preview = Image.open(uploaded_file)
            st.image(img_preview, caption="📎 Photo Attached", width=70)
            st.markdown('</div>', unsafe_allow_html=True)

    # 3. Chat Logic Handler (Triggers ONLY when Arrow is clicked or Enter is pressed with text)
    if (submit_clicked and user_prompt) or (user_prompt and "last_input" in st.session_state and st.session_state.last_input != user_prompt):
        st.session_state.last_input = user_prompt
        
        user_msg = {"role": "user", "content": user_prompt, "image": None}
        input_image = None
        
        if uploaded_file:
            input_image = Image.open(uploaded_file)
            user_msg["image"] = input_image
        
        st.session_state.messages.append(user_msg)
        
        # Generator API Request
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                if input_image:
                    response = model.generate_content([user_prompt, input_image])
                else:
                    response = model.generate_content(user_prompt)
                    
                ai_response = response.text
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # Clear states cleanly and refresh page layout
        st.rerun()
