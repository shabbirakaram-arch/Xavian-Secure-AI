import streamlit as st
import google.generativeai as genai
import os

# Page Configuration (Gemini Theme)
st.set_page_config(
    page_title="Xavian Secure AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Gemini-like UI Dark/Light adaptive look
st.markdown("""
    <style>
        /* Hide Streamlit Header and Footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main Title Styling */
        .gemini-title {
            font-size: 3rem;
            font-weight: 600;
            background: linear-gradient(45deg, #4285F4, #9B51E0, #EA4335);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 5px;
        }
        .gemini-subtitle {
            font-size: 1.2rem;
            color: #80868B;
            text-align: center;
            margin-bottom: 40px;
        }
        
        /* Chat Input Styling alignment */
        .stChatInputContainer {
            padding-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# App Header
st.markdown('<div class="gemini-title">Xavian Secure AI</div>', unsafe_allow_html=True)
st.markdown('<div class="gemini-subtitle">How can I help you today?</div>', unsafe_allow_html=True)

# Secure API Key Management (GitHub Secrets / Environment Variables)
# Local testing ke liye aap .env use kr skte ho, GitHub dynamic hosting ke liye Secrets me dalna hoga.
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    # Agar environment variable nahi milta toh input box dikhayega (Fallback)
    with st.expander("🔑 API Key Setup (Required if not set in Environment)", expanded=True):
        api_key = st.text_input("Enter your Gemini API Key:", type="password")
        st.caption("Get your key from Google AI Studio. For production, set it as 'GEMINI_API_KEY' in GitHub Secrets/Streamlit Cloud.")

# Initialize Gemini Model if API key is available
if api_key:
    genai.configure(api_key=api_key)
    # Using the standard stable flash/pro model
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Initialize chat history in session state if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask Xavian Secure AI..."):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate response from Gemini
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # Format context history for Gemini API
                # (Optional: optimization for multi-turn conversation)
                response = model.generate_content(prompt)
                full_response = response.text
                message_placeholder.markdown(full_response)
                
            except Exception as e:
                full_response = f"⚠️ Error: {str(e)}"
                message_placeholder.markdown(full_response)
                
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

else:
    st.info("Please provide a Gemini API Key to start the conversation.", icon="💡")
