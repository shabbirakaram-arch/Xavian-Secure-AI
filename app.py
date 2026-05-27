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

# --- CLEAN GEMINI-STYLE UI CSS ---
st.markdown("""
    <style>
    /* पूरे ऐप का बैकग्राउंड और फॉन्ट */
    .stApp {
        background-color: #131314;
        color: #e3e3e3;
    }
    
    /* मोबाइल स्क्रीन पर टाइटल को एक लाइन में फिट करने के लिए रेस्पॉन्सिव फॉन्ट */
    h1 {
        font-size: max(1.8rem, 4vw) !important;
        white-space: nowrap !important;
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
    
    /* Streamlit के डिफ़ॉल्ट हेडर, फुटर और मेनू को पूरी तरह छिपाने के लिए */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# मुख्य टाइटल
st.title("🛡️ Xavian Secure AI")

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

    # --- SIDEBAR (सारे टूल्स साइड में रहेंगे) ---
    uploaded_file = None
    with st.sidebar:
        st.markdown("### 🛠️ Media Tools")
        st.caption("यहाँ से आप फोटो या फाइल्स अपलोड कर सकते हैं")
        
        doc_file = st.file_uploader("➕ Files / Gallery / Lens", type=["jpg", "jpeg", "png", "pdf", "txt"], key="sidebar_uploader")
        
        st.markdown("---")
        st.markdown("🎙️ **Voice Input Guide:**\nअपने मोबाइल कीबोर्ड पर बने माइक (🎙️) आइकॉन को दबाकर बोलें, वह अपने आप यहाँ टाइप कर देगा।")

    # मीडिया हैंडलिंग
    if doc_file:
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
        
