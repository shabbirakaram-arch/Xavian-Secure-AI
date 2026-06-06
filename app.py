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
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed" # Default collapsed taaki full screen clean mile
)

# --- 3. PREMIUM ULTIMATE GEMINI INTERFACE EMULATION (CUSTOM CSS) ---
st.markdown("""
    <style>
    /* Gemini App Signature Dark Fluid Background */
    .stApp {
        background: radial-gradient(circle at bottom, #070913 0%, #030408 100%);
        color: #e3e3e3;
        padding-bottom: 120px !important;
    }
    
    /* Clean Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f1016 !important;
        border-right: 1px solid #1e2030;
    }
    
    /* Gemini Minimalist Top Heading Look */
    .gemini-title {
        font-size: 1.8rem;
        font-weight: 500;
        color: #e3e3e3;
        font-family: 'Google Sans', 'Segoe UI', system-ui, sans-serif;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 10px;
        margin-bottom: 30px;
    }
    
    /* Sub-Header Greeting (Ready when you are style) */
    .gemini-greeting {
        font-size: 2.2rem;
        font-weight: 400;
        color: #c4c7c5;
        text-align: center;
        margin-top: 15vh;
        margin-bottom: 5vh;
        font-family: 'Google Sans', system-ui, sans-serif;
    }
    
    /* Chat Message Bubbles - Micro Rounded borderless look */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 10px 0px !important;
        margin-bottom: 15px !important;
    }
    
    /* 🎯 PERFECT FLOATING BOTTOM INPUT BAR (GEMINI MATCH) */
    div[data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 30px !important;
        left: 5% !important;
        right: 5% !important;
        width: 90% !important;
        z-index: 999999;
        background-color: #1e1f20 !important;
        border-radius: 32px !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    
    /* Input textarea styling overrides */
    div[data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #e3e3e3 !important;
        border-radius: 32px !important;
    }
    
    /* Sidebar Security Terminal Box */
    .terminal-box {
        background-color: #000000;
        border: 1px solid #45a29e;
        border-radius: 6px;
        padding: 10px;
        font-family: 'Courier New', Courier, monospace;
        color: #66fcf1;
        font-size: 0.8rem;
    }
    
    /* Hide Default Streamlit Elements completely */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stFileUploader"] {margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

# --- 4. SECURE API KEY CONFIGURATION ---
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
    st.session_state.system_logs = ["Xavian System Ready. Interface loaded."]

# --- 6. SIDEBAR: CONTROL PANEL & SECURITY TERMINAL ONLY ---
with st.sidebar:
    st.markdown("### 🛡️ **Xavian Control Panel**")
    st.caption("Enterprise Agent Console")
    st.markdown("---")
    
    secret_input = st.text_input("Enter Activation Token:", type="password")
    if st.button("Verify Token", use_container_width=True):
        if secret_input == "activate_agent_xavian":
            st.session_state.agent_unlocked = True
            st.session_state.system_logs.append("SUCCESS: Agent core unlocked.")
            st.rerun()
        else:
            st.error("Invalid Token!")
            st.session_state.system_logs.append("ALERT: Auth failure.")
            
    if st.session_state.agent_unlocked:
        st.success("🤖 AGENT ON: STANDBY")
        if st.button("Lock Agent Core", type="primary", use_container_width=True):
            st.session_state.agent_unlocked = False
            st.session_state.system_logs.append("SYSTEM: Core locked.")
            st.rerun()
    else:
        st.info("📱 MODE: NORMAL CHAT")
        
    st.markdown("---")
    st.markdown("#### 📑 **Audit Logs**")
    log_content = "\n".join(st.session_state.system_logs[-5:])
    st.markdown(f'<div class="terminal-box">{log_content}</div>', unsafe_allow_html=True)

# --- 7. MAIN CLEAN INTERFACE (GEMINI STYLE) ---

# Top Bar header setup
st.markdown('<div class="gemini-title">✨ Xavian Secure AI</div>', unsafe_allow_html=True)

# Agar chat history khali hai, toh original Gemini greeting display karein
if not st.session_state.chat_history:
    st.markdown('<div class="gemini-greeting">Ready when you are</div>', unsafe_allow_html=True)

# Optional image attachment system
uploaded_image = st.file_uploader("Attach image (Optional)", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

# Render Messages cleanly
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message and message["image"] is not None:
            st.image(message["image"], width=250)

# Main Bottom Chat Box
if user_prompt := st.chat_input("Ask Gemini or execute automation..."):
    
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
        
        # AGENT ROUTING
        if st.session_state.agent_unlocked and ("install active directory" in prompt_lower or "configure firewall" in prompt_lower):
            response_placeholder.markdown("🔄 *Executing Executive Code Sequence...*")
            time.sleep(1.5)
            agent_res = "🚨 **[Interactive Alert]** Sir, configuration process complete ho chuka hai. Kya main rules cross-check karke save kar du?"
            response_placeholder.markdown(agent_res)
            st.session_state.chat_history.append({"role": "assistant", "content": agent_res})
            st.session_state.system_logs.append(f"COMMAND: Execution successful.")
        
        # NORMAL AI ENGINE
        else:
            if not api_configured:
                error_msg = "⚠️ **API Key Missing:** Kripya platform secrets check karein."
                response_placeholder.warning(error_msg)
                st.session_state.system_logs.append("ERROR: Token target failed.")
            else:
                response_placeholder.markdown("✨ *Thinking...*")
                try:
                    if input_img_obj:
                        ai_res = model.generate_content([user_prompt, input_img_obj])
                    else:
                        ai_res = model.generate_content(user_prompt)
                        
                    final_text = ai_res.text
                    response_placeholder.markdown(final_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": final_text})
                    st.session_state.system_logs.append("SUCCESS: Broadcast ok.")
                except Exception as e:
                    response_placeholder.error(f"API Error: {str(e)}")
                    st.session_state.system_logs.append(f"EXCEPTION.")
    
    st.rerun()
