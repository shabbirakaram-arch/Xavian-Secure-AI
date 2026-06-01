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

# --- CLEAN & ACCURATE GEMINI OVERLAY CSS ---
st.markdown("""
    <style>
    /* पूरे ऐप का बैकग्राउंड और फॉन्ट */
    .stApp {
        background-color: #131314;
        color: #e3e3e3;
    }
    
    h1 {
        font-size: max(1.8rem, 4vw) !important;
    }
    
    /* चैट बबल्स को जेमिनी डार्क थीम देना */
    div[data-testid="stChatMessage"] {
        background-color: #1e1f20 !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
    }
    div[data-testid="stChatMessage"] p {
        color: #ffffff !important;
        font-size: 16px !important;
    }
    
    /* --- THE MAGICAL OVERLAY HACK --- */
    /* असली चैट इनपुट बार को स्टाइल करना */
    div[data-testid="stChatInput"] {
        border: 1px solid #444746 !important;
        border-radius: 32px !important;
        background-color: #1e1f20 !important;
        padding-left: 50px !important; /* बाएं तरफ स्पेस छोड़ी ताकि प्लस बटन वहां बैठ सके */
    }
    
    div[data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    /* सेंड बटन को जेमिनी ब्लू लुक देना */
    button[data-testid="stChatInputSubmitButton"] {
        background-color: #1a73e8 !important;
        color: white !important;
        border-radius: 50% !important;
    }

    /* फ़ाइल अपलोडर को उठाकर सीधे चैट बार के ऊपर फिट करना */
    div[data-testid="stFileUploader"] {
        position: fixed;
        bottom: 30px; /* मोबाइल स्क्रीन के हिसाब से चैट बार की ऊंचाई पर सेट किया है */
        left: calc(50% - 315px); /* डेस्कटॉप पर चैट बार के बाएं कोने में रखने के लिए */
        width: 40px !important;
        z-index: 999999;
    }

    /* मोबाइल स्क्रीन्स के लिए प्लस बटन की पोजीशन को ऑटो-एडजस्ट करना */
    @media (max-width: 768px) {
        div[data-testid="stFileUploader"] {
            left: 25px !important;
            bottom: 24px !important;
        }
    }

    /* अपलोडर का फालतू डिफ़ॉल्ट लेआउट छिपाना */
    div[data-testid="stFileUploader"] section {
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
    }
    div[data-testid="stFileUploader"] section > input + div {
        display: none !important;
    }

    /* 'Browse Files' वाले बटन को सुंदर गोल '+' में बदलना */
    div[data-testid="stFileUploader"] button {
        background-color: #2b2c2e !important;
        color: #e3e3e3 !important;
        border: none !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        min-width: 36px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stFileUploader"] button::before {
        content: "+" !important;
        font-size: 20px !important;
        font-weight: bold !important;
    }
    div[data-testid="stFileUploader"] button span {
        display: none !important;
    }

    /* डिफ़ॉल्ट हेडर/फुटर हटाना */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# मुख्य टाइटल
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

    # 1. पुरानी चैट हिस्ट्री दिखाना
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message and message["image"] is not None:
                st.image(message["image"], use_container_width=True)

    # 2. फोटो प्रिव्यू कंटेनर (चैट बार के ठीक ऊपर)
    preview_container = st.container()

    # Voice Input गाइड
    st.markdown("🎙️ **Voice Input Guide:** अपने मोबाइल कीबोर्ड पर बने माइक (🎙️) आइकॉन को दबाकर बोलें।")

    # 3. प्लस बटन (File Uploader) - यह CSS की मदद से चैट इनपुट के बाएं कोने पर ओवरलैप हो जाएगा
    uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed", key="gemini_plus")

    # फोटो सेलेक्ट होने पर छोटा सा प्रिव्यू दिखाना
    if uploaded_file:
        with preview_container:
            img_preview = Image.open(uploaded_file)
            st.image(img_preview, caption="📎 फोटो अटैच हो चुकी है", width=90)

    # 4. असली स्टेबल चैट इनपुट बॉक्स
    if user_prompt := st.chat_input("Xavian Secure AI से कुछ भी पूछें..."):
        
        user_msg = {"role": "user", "content": user_prompt, "image": None}
        input_image = None
        
        if uploaded_file:
            input_image = Image.open(uploaded_file)
            user_msg["image"] = input_image
        
        # यूजर का मैसेज तुरंत सेव और शो करना
        st.session_state.messages.append(user_msg)
        with st.chat_message("user"):
            st.markdown(user_prompt)
            if input_image:
                st.image(input_image, use_container_width=True)
                
        # AI का रिस्पांस
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤖 *Xavian सोच रहा है...*")
            
            try:
                if input_image:
                    response = model.generate_content([user_prompt, input_image])
                else:
                    response = model.generate_content(user_prompt)
                    
                ai_response = response.text
                message_placeholder.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                error_msg = f"❌ एरर: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        st.rerun()
