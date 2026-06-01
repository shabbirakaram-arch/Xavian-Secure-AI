import os
import ssl
import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Network Fixes (SSL Errors se bachne ke liye)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ["PYTHONHTTPSVERIFY"] = "0"

# Streamlit Page Configuration
st.set_page_config(page_title="Xavian Secure AI", page_icon="🛡️", layout="centered")

# --- PERFECT GEMINI-STYLE UI CSS WITH OVERLAY PLUS BUTTON ---
st.markdown("""
    <style>
    /* Poore app ka background aur default text color */
    .stApp {
        background-color: #131314;
        color: #e3e3e3;
    }
    
    /* Responsive Title */
    h1 {
        font-size: max(1.8rem, 4vw) !important;
    }
    
    /* Chat bubbles ko Gemini Dark Theme jaisa look dena */
    div[data-testid="stChatMessage"] {
        background-color: #1e1f20 !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
    }
    div[data-testid="stChatMessage"] p, div[data-testid="stChatMessage"] span {
        color: #ffffff !important;
        font-size: 16px !important;
    }
    
    /* --- REAL CHAT INPUT OVERLAY HACK --- */
    /* Streamlit ke default chat input ke andar left side me space banana */
    div[data-testid="stChatInput"] {
        border: 1px solid #444746 !important;
        border-radius: 32px !important;
        background-color: #1e1f20 !important;
        padding-left: 55px !important; /* Is space me hi '+' button float karega */
    }
    
    div[data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    /* Send arrow button ko right side me circular aur blue karna */
    button[data-testid="stChatInputSubmitButton"] {
        background-color: #1a73e8 !important;
        color: white !important;
        border-radius: 50% !important;
    }

    /* --- STABLE FIXED PLUS BUTTON CSS --- */
    /* Upload div ko theek chat bar ke left side me overlay karna */
    div[data-testid="stFileUploader"] {
        position: fixed !important;
        bottom: 23px !important; 
        left: calc(50% - 325px) !important; 
        width: 44px !important;
        height: 44px !important;
        z-index: 9999999 !important; /* Taki click karne par sidhe gallery khule */
    }

    /* Mobile screens ke liye overlay position ko auto-adjust karna */
    @media (max-width: 768px) {
        div[data-testid="stFileUploader"] {
            left: 20px !important;
            bottom: 21px !important;
        }
    }

    /* File uploader ka default "Drag & Drop" aur borders hatana */
    div[data-testid="stFileUploader"] section {
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
        width: 44px !important;
        height: 44px !important;
    }
    div[data-testid="stFileUploader"] section > input + div {
        display: none !important;
    }

    /* Default button ko ek gool '+' icon me badalna */
    div[data-testid="stFileUploader"] button {
        background-color: #2b2c2e !important;
        color: #e3e3e3 !important;
        border: none !important;
        border-radius: 50% !important;
        width: 38px !important;
        height: 38px !important;
        min-width: 38px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        pointer-events: auto !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.3) !important;
    }
    div[data-testid="stFileUploader"] button::before {
        content: "+" !important;
        font-size: 22px !important;
        font-weight: bold !important;
    }
    div[data-testid="stFileUploader"] button span {
        display: none !important; /* Purane 'Browse files' text ko chupane ke liye */
    }

    /* Image preview container margin adjustments */
    .preview-wrapper-box {
        margin-bottom: 15px;
    }

    /* Default Headers/Footers ko poori tarah hide rakhna */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Main App Title
st.title("🛡️ Xavian Secure AI")

# Streamlit Secrets se API key check karna
if "GEMINI_SECRET_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_SECRET_KEY"]
    os.environ["GEMINI_SECRET_KEY"] = api_key
    genai.configure(api_key=api_key)
else:
    api_key = None

if not api_key:
    st.error("❌ Error: Streamlit Secrets mein API Key गायब है!")
else:
    # Model initialize karna
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Session State Initialize karna chat history ke liye
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 1. Chat History Render karna
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message and message["image"] is not None:
                st.image(message["image"], use_container_width=True)

    # 2. Floating Photo Preview Container (Chat bar ke theek upar)
    preview_container = st.container()

    # Voice Input Guide Line
    st.markdown("🎙️ **Voice Input Guide:** Apne mobile keyboard ke mike (🎙️) icon ko daba kar bolein.")

    # --- 3. NO-REFRESH FRAGMENT BASED PHOTO UPLOAD ZONE ---
    # Is decorative function se photo upload hote hi poora webpage refresh nahi hoga, jisse keyboard automatic popup nahi hoga.
    @st.fragment
    def render_plus_button():
        uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed", key="gemini_stable_plus")
        if uploaded_file:
            # File ko background me session state me store kar lena taaki chat input ise use kar sake
            st.session_state["active_upload_file"] = uploaded_file

    # Plus button render karna (CSS ise chat bar ke left me fit karegi)
    render_plus_button()

    # Agar photo successfully uploaded hai toh chat input ke upar uska preview dikhana
    if "active_upload_file" in st.session_state and st.session_state["active_upload_file"] is not None:
        with preview_container:
            st.markdown('<div class="preview-wrapper-box">', unsafe_allow_html=True)
            img_preview = Image.open(st.session_state["active_upload_file"])
            st.image(img_preview, caption="📎 Photo भेजने ke liye taiyaar hai", width=100)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. CHAT INPUT AND MAIN LOGIC PROCESSING ---
    if user_prompt := st.chat_input("Xavian Secure AI se kuch bhi poochein..."):
        
        # User message ka dictionary object banana
        user_msg = {"role": "user", "content": user_prompt, "image": None}
        input_image = None
        
        # Agar session state me koi image uploaded padi hai toh use uthana
        if "active_upload_file" in st.session_state and st.session_state["active_upload_file"] is not None:
            input_image = Image.open(st.session_state["active_upload_file"])
            user_msg["image"] = input_image
        
        # Screen par instant user response append aur display karna
        st.session_state.messages.append(user_msg)
        with st.chat_message("user"):
            st.markdown(user_prompt)
            if input_image:
                st.image(input_image, use_container_width=True)
                
        # Gemini API Request Call karna aur Assistant response dikhana
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤖 *Xavian soch raha hai...*")
            
            try:
                if input_image:
                    response = model.generate_content([user_prompt, input_image])
                else:
                    response = model.generate_content(user_prompt)
                    
                ai_response = response.text
                message_placeholder.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                error_msg = f"❌ System Error aaya hai: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # Message send hone ke baad background se uploaded file ko saaf karna taaki agli chat fresh ho ske
        if "active_upload_file" in st.session_state:
            st.session_state["active_upload_file"] = None
            
        # UI refresh click clear karne ke liye
        st.rerun()
