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
    page_title="Xavian Secure AI Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. PREMIUM ENTERPRISE DARK THEME CUSTOM CSS ---
st.markdown("""
    <style>
    /* Main Background and Text Color */
    .stApp {
        background-color: #0d0e12;
        color: #e2e8f0;
    }
    
    /* Clean Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #151821 !important;
        border-right: 1px solid #262936;
    }
    
    /* Professional Header/Title */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #3b82f6, #1d4ed8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    
    /* System Logs Terminal Box */
    .terminal-box {
        background-color: #050507;
        border: 1px solid #22c55e;
        border-radius: 8px;
        padding: 15px;
        font-family: 'Courier New', Courier, monospace;
        color: #22c55e;
        margin-bottom: 20px;
    }
    
    /* Chat Bubbles Style */
    div[data-testid="stChatMessage"] {
        background-color: #161922 !important;
        border: 1px solid #232736 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 12px !important;
    }
    
    /* Hide Default Streamlit Artifacts */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. SECURE API KEY CONFIGURATION ---
# GitHub standards ke mutabik API key secrets se load hogi
if "GEMINI_SECRET_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_SECRET_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

# --- 5. INITIALIZE STATE MANAGEMENT ---
if "agent_unlocked" not in st.session_state:
    st.session_state.agent_unlocked = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "system_logs" not in st.session_state:
    st.session_state.system_logs = ["System Initialized. Awaiting secure authentication..."]

# --- 6. SIDEBAR: CONTROL CENTER & SECRET AUTHENTICATION ---
with st.sidebar:
    st.image("https://img.icons8.com/lounge/100/shield.png", width=70)
    st.markdown("### **Xavian Control Center**")
    st.caption("Enterprise IT Automation & AI Agent Platform")
    st.markdown("---")
    
    # Target Architecture Indicator
    st.markdown("#### **Platform Status**")
    if st.session_state.agent_unlocked:
        st.success("🤖 AGENT MODE: UNLOCKED (Laptop)")
    else:
        st.info("📱 NORMAL MODE: ACTIVE (Mobile/Web)")
        
    st.markdown("---")
    
    # Secret Authentication Section
    st.markdown("#### **Security Authentication**")
    secret_input = st.text_input("Enter Token Code:", type="password", help="Enter secret code to unlock Phase 2 Agent Automation.")
    
    if st.button("Authenticate System", use_container_width=True):
        if secret_input == "activate_agent_xavian": # Aapka set kiya hua secret code
            st.session_state.agent_unlocked = True
            st.session_state.system_logs.append("SUCCESS: Token code verified. Agent core stand-by.")
            st.rerun()
        else:
            st.error("Invalid Secret Token!")
            st.session_state.system_logs.append("WARNING: Unauthorized authentication attempt detected.")
            
    if st.session_state.agent_unlocked:
        if st.button("Lock Agent Core", type="primary", use_container_width=True):
            st.session_state.agent_unlocked = False
            st.session_state.system_logs.append("SYSTEM: Agent core locked manually by Administrator.")
            st.rerun()

# --- 7. MAIN DASHBOARD INTERFACE ---
col_main, col_logs = st.columns([0.7, 0.3])

with col_main:
    st.markdown('<div class="main-title">🛡️ Xavian Secure AI Platform</div>', unsafe_allow_html=True)
    
    # Image Attachment Option (Phase 1 Multimodal Feature)
    uploaded_image = st.file_uploader("Attach Image for Analysis (Optional)", type=["png", "jpg", "jpeg"])
    
    # Rendering Chat History
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message and message["image"] is not None:
                st.image(message["image"], width=300)

    # Main Input Prompt
    if user_prompt := st.chat_input("Ask a question or enter core system command..."):
        
        # Capture input state
        current_msg = {"role": "user", "content": user_prompt, "image": None}
        input_img_obj = None
        
        if uploaded_image:
            input_img_obj = Image.open(uploaded_image)
            current_msg["image"] = input_img_obj
            
        st.session_state.chat_history.append(current_msg)
        
        # Instantly render user query
        with st.chat_message("user"):
            st.markdown(user_prompt)
            if input_img_obj:
                st.image(input_img_obj, width=300)
                
        # Processing Response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            # CHECK ROUTING: Agent Core Mode vs Normal Chat Mode
            prompt_lower = user_prompt.lower()
            if st.session_state.agent_unlocked and ("install active directory" in prompt_lower or "configure firewall" in prompt_lower):
                
                # Phase 2 & 3 Framework Trigger Simulation
                response_placeholder.markdown("🔄 *Executing Executive Automation Script...*")
                st.session_state.system_logs.append(f"EXECUTE: Command received -> {user_prompt}")
                time.sleep(2)
                
                agent_msg = "🚨 **[Interactive Alert]** Sir, configuration process complete ho chuka hai. Kya main rules apply karke save kar du?"
                response_placeholder.markdown(agent_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": agent_msg})
                st.session_state.system_logs.append("WAITING: Awaiting confirmation ('Cross check karke save karo').")
                
            else:
                # Normal AI Engine Processing (Phase 1)
                if not model:
                    err = "❌ API Error: GEMINI_SECRET_KEY not configured in Streamlit Secrets."
                    response_placeholder.error(err)
                else:
                    response_placeholder.markdown("🤖 *Xavian is thinking...*")
                    try:
                        if input_img_obj:
                            ai_res = model.generate_content([user_prompt, input_img_obj])
                        else:
                            ai_res = model.generate_content(user_prompt)
                            
                        final_text = ai_res.text
                        response_placeholder.markdown(final_text)
                        st.session_state.chat_history.append({"role": "assistant", "content": final_text})
                        st.session_state.system_logs.append("SUCCESS: Gemini response generated successfully.")
                    except Exception as e:
                        response_placeholder.error(f"API Exception: {str(e)}")
                        st.session_state.system_logs.append(f"ERROR: API Exception -> {str(e)}")
        
        st.rerun()

# --- 8. RIGHT SIDEBAR: REAL-TIME SYSTEM AUDIT LOGS ---
with col_logs:
    st.markdown("#### 📑 **System Security Logs**")
    st.caption("Real-time terminal tracking for compliance & auditing.")
    
    # Creating a scrolling terminal look
    log_content = "\n".join(st.session_state.system_logs[-10:]) # Shows last 10 logs
    st.markdown(f'<div class="terminal-box">{log_content}</div>', unsafe_allow_html=True)
    
    # Information Box for Phase Roadmap
    st.info("""
    **Developer Notice (GitHub Roadmap):**
    - **Phase 1:** Enabled (Normal AI + Image support).
    - **Phase 2 & 3:** Under staging. Activate via secret token in the sidebar to simulate Human-in-the-loop pipeline.
    """)
    
