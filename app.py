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

# --- CLEAN GEMINI-STYLE UI CSS ---
st.markdown("""
    <style>
    /* पूरे ऐप का बैकग्राउंड और फॉन्ट */
    .stApp {
        background-color: #131314;
        color: #e3e3e3;
    }
    
    /* मोबाइल स्क्रीन पर टाइटल को एक line में फिट करने के लिए रेस्पॉन्सिव फॉन्ट */
    h1 {
        font-size: max(1.8rem, 4vw) !important;
        white-space: nowrap !important;
    }
    
    /* चैट के अंदर आने वाले टेक्स्ट को एकदम साफ़ और सफेद दिखाने के लिए */
    div[data-testid="stChatMessage"] p, div[data-testid="stChatMessage"] span {
        color: #ffffff !important;
        font-size: 16px !important;
    }
    
    /* चैट ब्लॉक का बैकग्राउंड थोड़ा सा हल्का डार्क करना */
    div[data-testid="stChatMessage"] {
        background-color: #1e1f20 !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
    }
    
    /* चैट इनपुट कंटेनर को जेमिनी जैसा राउंड और बैकग्राउंड देना */
    div[data-testid="stChatInput"] {
        border: 1px solid #444746 !important;
        border-radius: 32px !important;
        background-color: #1e1f20 !important;
        padding-left: 10px !important;
        padding-right: 10px !important;
    }
    
    /* इनपुट बॉक्स में टाइप होने वाले टेक्स्ट को मोबाइल और डेस्कटॉप दोनों पर 100% सफेद करने के लिए */
    div[data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 500 !important;
    }
    
    /* Placeholder टेक्स्ट को थोड़ा सा विज़िबल करना */
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #aaa !important;
        -webkit-text-fill-color: #aaa !important;
    }
    
    /* सेंड बटन को ब्लू और गोल करना */
    button[data-testid="stChatInputSubmitButton"] {
        background-color: #1a73e8 !important;
        color: white !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
    }
    
    /* Streamlit के डिफ़ॉल्ट हेडर, फुटर और मेनू को पूरी तरह छिपाने के लिए */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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
    # Gemini Model Initialize करना
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Session State Initialize करना
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 1. पहले पुरानी चैट हिस्ट्री दिखाएं (बिना किसी इनपुट बॉक्स के)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message and message["image"] is not None:
                st.image(message["image"], use_container_width=True)

    st.markdown("---")
    
    # 2. फ़ोटो अपलोड सेक्शन (चैट के नीचे एक ही बार दिखेगा)
    uploaded_file = st.file_uploader("📸 Attach a photo (Optional):", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        preview_img = Image.open(uploaded_file)
        st.image(preview_img, caption="📎 सिलेक्टेड फोटो भेजने के लिए तैयार है", width=150)

    st.markdown("🎙️ **Voice Input Guide:** अपने मोबाइल कीबोर्ड पर बने माइक (🎙️) आइकॉन को दबाकर बोलें।")

    # 3. अकेला और असली चैट इनपुट बॉक्स
    if user_prompt := st.chat_input("Xavian Secure AI से कुछ भी पूछें..."):
        
        # User का मैसेज ऑब्जेक्ट तैयार करना
        user_msg = {"role": "user", "content": user_prompt, "image": None}
        
        # अगर इमेज अपलोडेड है तो उसे सेव करना
        input_image = None
        if uploaded_file:
            input_image = Image.open(uploaded_file)
            user_msg["image"] = input_image
        
        # स्क्रीन पर यूजर का मैसेज तुरंत दिखाना
        st.session_state.messages.append(user_msg)
        with st.chat_message("user"):
            st.markdown(user_prompt)
            if input_image:
                st.image(input_image, use_container_width=True)
                
        # Assistant (AI) का जवाब जनरेट करना
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
                
                # AI का जवाब हिस्ट्री में सेव करना
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                error_msg = f"❌ सिस्टम एरर: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # पेज को रिफ्रेश करना ताकि UI सही से अपडेट हो जाए
        st.rerun()
        
