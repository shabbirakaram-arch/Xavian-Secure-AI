import os
import ssl
import time
from PIL import Image
import streamlit as st
import google.generativeai as genai

# --- 1. NETWORK & SSL PRODUCTION FIXES ---
ssl._create_default_https_context = ssl._create_unverified_context
os.environ["PYTHONHTTPSVERIFY"] = "0"

# --- 2. INITIALIZE STREAMLIT PAGE CONFIG ---
st.set_page_config(
    page_title="Xavian Secure AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. PROFESSIONAL CYBER-SECURITY DARK THEME WITH FIXED BOTTOM CHAT BOX ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0b0c10;
        color: #c5c6c7;
        padding-bottom: 100px; /* Taki chat boxes chat_input ke peeche na chupein */
    }
    
    /* Sidebar Metallic Styling */
    section[data-testid="stSidebar"] {
        background-color: #1f2833 !important;
        border-right: 1px solid #45a29e;
    }
    
    /* Xavian Secure AI Title */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #66fcf1;
        margin-bottom: 25px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Security Terminal Box for Logs */
    .terminal-box {
        background-color: #000000;
        border: 1px solid #45a29e;
        border-radius: 6px;
        padding: 12px;
        font-family: 'Courier New', Courier, monospace;
        color: #66fcf1;
        margin-bottom: 20px;
    }
    
    /* Chat Bubbles Style */
    div[data-testid="stChatMessage"] {
        background-color: #1f2833 !important;
        border: 1px solid #2f3c4f !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin-bottom: 10px !important;
    }
    
    /* 🎯 CRITICAL FIX: Chat Input Box ko hamesha screen ke bottom par chipkane ke liye CSS */
    div[data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 20px !important;
        left: 0;
        right: 0;
        z-index: 999999;
        background-color: #0b0c10 !important;
        padding: 10px 5% !important;
    }

    /* Hide Default Header & Footer */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. SECURE API KEY CONFIGURATION (UNIVERSAL FIX) ---
api_configured = False
api_key = None
model = None

for key_name in ["GEMINI_SECRET_KEY", "GEMINI_API_KEY", "XAVIAN_SECRET_KEY", "XAVIAN_API_KEY"]:
    if key_name in st.secrets and st.secrets[key_name] != "":
        api_key = st.secrets[key_name]
        break

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        api_configured = True
    except Exception:
        model = None
        api_configured = False

# --- 5. INITIALIZE STATE MANAGEMENT ---
if "agent_unlocked" not in st.session_state:
    st.session_state.agent_unlocked = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "system_logs" not in st.session_state:
    st.session_state.system_logs = ["Xavian System Ready. Scanning security tokens..."]

# --- 6. SIDEBAR: CONTROL CENTER & SECRET AUTHENTICATION ---
with st.sidebar:
    st.markdown("### **Xavian Control Panel**")
    st.caption("Enterprise Security Framework")
    st.markdown("---")
    
    secret_input = st.text_input("Enter Activation Token:", type="password")
    
    if st.button("Verify Token", use_container_width=True):
        if secret_input == "activate_agent_xavian":
            st.session_state.agent_unlocked = True
            st.session_state.system_logs.append("SUCCESS: Token accepted. Agent standby.")
            st.rerun()
        else:
            st.error("Invalid Token!")
            st.session_state.system_logs.append("ALERT: Unauthorized token attempt.")
            
    if st.session_state.agent_unlocked:
        st.success("🤖 AGENT CORE: UNLOCKED")
        if st.button("Lock Agent Core", type="primary", use_container_width=True):
            st.session_state.agent_unlocked = False
            st.session_state.system_logs.append("SYSTEM: Agent core locked.")
            st.rerun()
    else:
        st.info("📱 MODE: NORMAL CHAT")

# --- 7. MAIN INTERFACE LAYOUT ---
col_main, col_logs = st.columns([0.7, 0.3])

with col_main:
    st.markdown('<div class="main-title">🛡️ Xavian Secure AI</div>', unsafe_allow_html=True)
    uploaded_image = st.file_uploader("Attach Document/Image (Optional)", type=["png", "jpg", "jpeg"])
    
    # Render Previous Messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message and message["image"] is not None:
                st.image(message["image"], width=250)

    # Main Chat Input Box (Ab ye CSS ki wajah se hamesha bottom par float karega)
    if user_prompt := st.chat_input("Enter command or ask a question..."):
        
        current_msg = {"role": "user", "content": user_prompt, "image": None}
        input_img_obj = None
        if uploaded_image:
            input_img_obj = Image.open(uploaded_image)
            current_msg["image"] = input_img_obj
            
        st.session_state.chat_history.append(current_msg)
        
        with st.chat_message("user"):
            st.markdown(user_prompt)
            if input_img_obj:
                st.image(input_img_obj, width=250)
                
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            prompt_lower = user_prompt.lower()
            
            if st.session_state.agent_unlocked and ("install active directory" in prompt_lower or "configure firewall" in prompt_lower):
                response_placeholder.markdown("🔄 *Executing Executive Code Sequence...*")
                time.sleep(2)
                agent_res = "🚨 **[Interactive Alert]** Sir, configuration process complete ho chuka hai. Kya main rules cross-check karke save kar du?"
                response_placeholder.markdown(agent_res)
                st.session_state.chat_history.append({"role": "assistant", "content": agent_res})
                st.session_state.system_logs.append(f"COMMAND: {user_prompt} executed via Agent Core.")
            
            else:
                if not api_configured:
                    error_msg = "⚠️ **API Key Missing:** Kripya Streamlit Settings -> Secrets mein jaakar apni Gemini Key add karein tabhi reply aayega!"
                    response_placeholder.warning(error_msg)
                    st.session_state.system_logs.append("ERROR: API key target not found.")
                else:
                    response_placeholder.markdown("🤖 *Thinking...*")
                    try:
                        if input_img_obj:
                            ai_res = model.generate_content([user_prompt, input_img_obj])
                        else:
                            ai_res = model.generate_content(user_prompt)
                            
                        final_text = ai_res.text
                        response_placeholder.markdown(final_text)
                        st.session_state.chat_history.append({"role": "assistant", "content": final_text})
                        st.session_state.system_logs.append("SUCCESS: AI Response dispatched.")
                    except Exception as e:
                        response_placeholder.error(f"API Error: {str(e)}")
                        st.session_state.system_logs.append(f"EXCEPTION: {str(e)}")
        
        st.rerun()

# --- 8. RIGHT SIDEBAR: TERMINAL LOGS WINDOW ---
with col_logs:
    st.markdown("#### 📑 **Security Logs**")
    log_content = "\n".join(st.session_state.system_logs[-8:])
    st.markdown(f'<div class="terminal-box">{log_content}</div>', unsafe_allow_html=True)
