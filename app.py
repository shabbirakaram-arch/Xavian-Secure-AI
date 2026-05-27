import os
import ssl
import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Pydroid 3 Network Setup & Fixes
ssl._create_default_https_context = ssl._create_unverified_context
os.environ["PYTHONHTTPSVERIFY"] = "0"

# 2. Secure Environment Configuration
os.environ["GEMINI_SECRET_KEY"] = st.secrets["GEMINI_SECRET_KEY"]

# Streamlit Page Setup
st.set_page_config(page_title="Xavian Secure AI", page_icon="🛡️", layout="centered")

# CSS: Enter बटन को ब्लू करने के लिए और UI को सुंदर बनाने के लिए custom style
st.markdown("""
    <style>
    /* Chat input button color to Blue */
    button[data-testid="stChatInputSubmitButton"] {
        background-color: #1E90FF !important;
        color: white !important;
    }
    /* Fixed container for custom control buttons at the bottom */
    .stHorizontalBlock {
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Xavian Secure AI")
st.caption("A Secure & Powerful Web Assistant powered by Gemini 2.5")

# Fetch key from environment
api_key = os.environ.get("GEMINI_SECRET_KEY")

if not api_key:
    st.error("❌ Error: Kripya pehle Streamlit Secrets me apni asli API Key dalein!")
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
            if "image" in message:
                st.image(message["image"], caption="Uploaded Media", use_container_width=True)

    # 3. Sidebar ya Top Control for Multimodal Features (+ icon substitute)
    st.markdown("### ➕ Add Media & Voice")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    uploaded_file = None
    voice_text = ""

    with col1:
        # Camera / Lens Feature
        img_file = st.file_uploader("📸 Lens/Camera", type=["jpg", "jpeg", "png"], key="camera")
    with col2:
        # Gallery / File Feature
        doc_file = st.file_uploader("📁 Gallery/Files", type=["jpg", "jpeg", "png", "pdf", "txt"], key="files")
    with col3:
        # Voice Input Emulation (Streamlit provides text fallback, using voice note instructions)
        voice_active = st.checkbox("🎙️ Voice Mode")
        if voice_active:
            st.info("💡 Mobile Keyboard का Mic (🎙️) दबाकर बोलें, वह अपने आप टेक्स्ट लिख देगा!")

    # Combine file selection
    if img_file:
        uploaded_file = img_file
    elif doc_file:
        uploaded_file = doc_file

    # Show small preview of attached file if any
    if uploaded_file and uploaded_file.type.startswith("image/"):
        preview_img = Image.open(uploaded_file)
        st.image(preview_img, caption="Attached Image", width=150)

    # User Input Box
    if prompt := st.chat_input("Xavian Secure AI se kuch bhi poohein..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        user_msg = {"role": "user", "content": prompt}
        if uploaded_file and uploaded_file.type.startswith("image/"):
            user_msg["image"] = Image.open(uploaded_file)
            
        st.session_state.messages.append(user_msg)

        # Generate Response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤖 *Xavian soch raha hai...*")
            
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # If image is attached, send to model with prompt
                if uploaded_file and uploaded_file.type.startswith("image/"):
                    img_data = Image.open(uploaded_file)
                    response = model.generate_content([prompt, img_data])
                else:
                    response = model.generate_content(prompt)
                    
                full_response = response.text
                message_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"❌ System Error: {str(e)}"
                message_placeholder.markdown(full_response)
                
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        # Rerun to clear the uploaded file cache after sending
        st.rerun()
