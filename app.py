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

# --- GEMINI UI WITH INTEGRATED '+' UPLOAD BUTTON ---
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
    
    /* चैट मैसेजेस की स्टाइलिंग */
    div[data-testid="stChatMessage"] p {
        color: #ffffff !important;
        font-size: 16px !important;
    }
    div[data-testid="stChatMessage"] {
        background-color: #1e1f20 !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
    }

    /* --- GEMINI BAR HACK (Flex Container for Upload + Chat) --- */
    /* इस कंटेनर की मदद से अपलोड बटन और चैट बॉक्स एक लाइन में आ जाते हैं */
    .gemini-bar-container {
        display: flex;
        align-items: center;
        gap: 10px;
        background-color: #1e1f20;
        border: 1px solid #444746;
        border-radius: 32px;
        padding: 4px 14px;
        margin-top: 10px;
    }

    /* Streamlit के इनपुट बॉक्स की अपनी बॉर्डर और बैकग्राउंड को हटाना ताकि वह हमारे कंटेनर में फिट हो सके */
    div[data-testid="stChatInput"] {
        border: none !important;
        background-color: transparent !important;
        padding: 0 !important;
        flex-grow: 1;
    }
    
    div[data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    /* सेंड बटन को जेमिनी लुक देना */
    button[data-testid="stChatInputSubmitButton"] {
        background-color: #1a73e8 !important;
        color: white !important;
        border-radius: 50% !important;
    }

    /* फ़ाइल अपलोडर के डिफ़ॉल्ट टेक्स्ट और फालतू डिज़ाइन को छिपाना */
    div[data-testid="stFileUploader"] section {
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
    }
    div[data-testid="stFileUploader"] section > input + div {
        display: none !important; /* 'Drag and drop' टेक्स्ट छिपाने के लिए */
    }

    /* अपलोड बटन को गोल '+' आइकॉन में बदलना */
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
        font-size: 20px !important;
        padding: 0 !important;
        box-shadow: none !important;
    }
    
    /* बटन के डिफ़ॉल्ट टेक्स्ट को '+' से बदल देना */
    div[data-testid="stFileUploader"] button::before {
        content: "+" !important;
        font-size: 22px !important;
        font-weight: bold !important;
    }
    div[data-testid="stFileUploader"] button span {
        display: none !important; /* पुराने 'Browse files' टेक्स्ट को गायब करना */
    }

    /* छुपे हुए फुटर एलिमेंट्स */
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

    # 1. चैट हिस्ट्री डिस्प्ले करना
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message and message["image"] is not None:
                st.image(message["image"], use_container_width=True)

    st.markdown("---")
    
    # 2. सिलेक्टेड फोटो का छोटा सा प्रिव्यू (यदि फोटो अपलोड की गई हो)
    # इसे इनपुट बार के ठीक ऊपर रखा है ताकि यूजर को पता चले कि फोटो अटैच हो चुकी है
    preview_placeholder = st.container()

    # Voice Input गाइड
    st.markdown("🎙️ **Voice Input Guide:** अपने मोबाइल कीबोर्ड पर बने माइक (🎙️) आइकॉन को दबाकर बोलें।")

    # 3. HTML Div कंटेनर की शुरुआत जो अपलोडर और इनपुट बॉक्स को एक साथ बांधेगा
    st.markdown('<div class="gemini-bar-container">', unsafe_allow_html=True)
    
    # यहाँ हमारा '+' बटन (File Uploader) लोड होगा
    uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    
    # यहाँ हमारा मुख्य चैट इनपुट बॉक्स लोड होगा
    user_prompt = st.chat_input("Xavian Secure AI से कुछ भी पूछें...")
    
    st.markdown('</div>', unsafe_allow_html=True) # HTML Container बंद

    # प्रिव्यू दिखाने का लॉजिक
    if uploaded_file:
        with preview_placeholder:
            img_preview = Image.open(uploaded_file)
            st.image(img_preview, caption="📎 फोटो भेजने के लिए तैयार है", width=100)

    # 4. चैट प्रोसेसिंग लॉजिक
    if user_prompt:
        user_msg = {"role": "user", "content": user_prompt, "image": None}
        input_image = None
        
        if uploaded_file:
            input_image = Image.open(uploaded_file)
            user_msg["image"] = input_image
        
        st.session_state.messages.append(user_msg)
        
        # यूज़र का इनपुट तुरंत स्क्रीन पर रिफ्रेश करना
        with st.chat_message("user"):
            st.markdown(user_prompt)
            if input_image:
                st.image(input_image, use_container_width=True)
                
        # AI का रिस्पांस जनरेट करना
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
                error_msg = f"❌ सिस्टम एरर: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        st.rerun()
        
