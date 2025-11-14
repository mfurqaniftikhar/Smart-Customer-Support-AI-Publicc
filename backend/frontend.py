import streamlit as st
from streamlit_chat import message
import requests
import pandas as pd
from datetime import datetime
import re
import speech_recognition as sr
from gtts import gTTS
import os
import tempfile
import base64

st.set_page_config(page_title="Customer Support System", page_icon="🚀", layout="wide")

# Admin credentials
ADMIN_USERNAME = "furqan"
ADMIN_PASSWORD = "furqan00"

# Backend API URL
API_BASE_URL = "http://127.0.0.1:8000"

# ------------------------
# Voice Functions
# ------------------------
def speech_to_text():
    """Convert speech to text using microphone"""
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... Please speak now!")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, phrase_time_limit=15)
            
            with st.spinner("🔄 Converting speech to text..."):
                text = recognizer.recognize_google(audio, language='en-US')
                return text
    except sr.WaitTimeoutError:
        return "⏱️ No speech detected. Please try again."
    except sr.UnknownValueError:
        return "❌ Could not understand audio. Please speak clearly."
    except sr.RequestError as e:
        return f"❌ Speech service error: {str(e)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def text_to_speech(text, lang='en'):
    """Convert text to speech and return audio file path"""
    try:
        # Clean text from markdown and special characters
        clean_text = re.sub(r'[#*_~`]', '', text)
        clean_text = re.sub(r'\[.*?\]\(.*?\)', '', clean_text)
        clean_text = re.sub(r'---', '', clean_text)
        clean_text = re.sub(r'[📍🏪📞📧🌐🛍️✅💰💬🎉🚀📦🏢🔍📊🎭💫📖🔊▶️📝🆕🔁👤🔐🏠⬅️💡🎤🔇🏡📋📥👥💻]', '', clean_text)
        
        # Limit text length
        if len(clean_text) > 500:
            clean_text = clean_text[:500] + "..."
        
        if not clean_text.strip():
            return None
            
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")
        return None

def play_audio(file_path):
    """Play audio file with auto-play"""
    try:
        with open(file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        
        audio_base64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
        
        # Clean up temp file
        try:
            os.unlink(file_path)
        except:
            pass
            
    except Exception as e:
        st.error(f"Error playing audio: {str(e)}")

# ------------------------
# Initialize session state
# ------------------------
if "mode" not in st.session_state:
    st.session_state.mode = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "show_order_form" not in st.session_state:
    st.session_state.show_order_form = False
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "first_message" not in st.session_state:
    st.session_state.first_message = True
if "business_details_shown" not in st.session_state:
    st.session_state.business_details_shown = False
if "voice_mode" not in st.session_state:
    st.session_state.voice_mode = False
if "last_bot_response" not in st.session_state:
    st.session_state.last_bot_response = ""
if "auto_play_response" not in st.session_state:
    st.session_state.auto_play_response = False
if "company_setup_done" not in st.session_state:
    st.session_state.company_setup_done = False
if "company_profile" not in st.session_state:
    st.session_state.company_profile = None
if "show_company_setup" not in st.session_state:
    st.session_state.show_company_setup = False

# ------------------------
# ORDER DETECTION KEYWORDS
# ------------------------
ORDER_KEYWORDS = [
    "order", "buy", "purchase", "get", "want to order",
    "i need", "khareedna", "mangwana", "lena hai",
    "chahiye", "order karna", "book karna", "mujy aik peice chiya",
    "yes", "haan", "ha", "sure", "ok", "okay", "bilkul"
]

def detect_order_intent(text):
    """Check if user wants to place an order"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in ORDER_KEYWORDS)

def get_business_details():
    """Fetch business details - either from company profile or default"""
    
    # Check if company profile exists
    if st.session_state.company_setup_done and st.session_state.company_profile:
        profile = st.session_state.company_profile
        
        company_name = profile.get("company_name", "Our Company")
        tagline = profile.get("tagline", "")
        about = profile.get("short_about", "")
        products = profile.get("products", [])
        website = profile.get("website", "")
        contact_email = profile.get("contact_email", "")
        contact_phone = profile.get("contact_phone", "")
        address = profile.get("address", "")
        
        # Build dynamic business details from company profile
        details = f"""
📍 **Company Information:**

🏪 **Company:** {company_name}
"""
        
        if tagline:
            details += f"💫 **Tagline:** {tagline}\n"
        
        if website:
            details += f"🌐 **Website:** {website}\n"
        
        if contact_email:
            details += f"📧 **Email:** {contact_email}\n"
            
        if contact_phone:
            details += f"📞 **Phone:** {contact_phone}\n"
            
        if address:
            details += f"🏢 **Address:** {address}\n"
        
        if about:
            details += f"\n📖 **About Us:**\n{about}\n"
        
        if products:
            details += f"\n🛍️ **Our Products/Services:**\n"
            for i, product in enumerate(products[:5], 1):
                details += f"✅ {product}\n"
        
        details += f"""
💬 **Get in Touch:**
We're here to help you with any questions about our products and services!
"""
        
        return details
    
    else:
        return """
📍 **Our Business Details:**

🏪 **Company:** Premium Products Store
📞 **Contact:** +92 300 1234567
📧 **Email:** support@premiumstore.com
🌐 **Website:** www.premiumstore.com

🛍️ **What We Offer:**
✅ High-quality products
✅ Fast delivery (2-3 business days)
✅ Cash on Delivery available
✅ 7-day return policy
✅ 24/7 customer support

💰 **Payment Methods:** Cash on Delivery, Bank Transfer, JazzCash, EasyPaisa
"""

# ========================================
# MODE SELECTION (Landing Page)
# ========================================
if st.session_state.mode is None:
    st.markdown("""
    <style>
        .main-title {
            text-align: center;
            color: #1f77b4;
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            font-size: 1.2em;
            margin-bottom: 40px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-title">🚀 AI Customer Support System</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Powered by Advanced AI Technology (Ollama + RAG)</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Welcome! Please select your portal")
        st.markdown("")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("#### 🤖 Customer Portal")
            st.markdown("""
            - Chat with AI bot (Ollama)
            - 🎤 Voice chat support
            - 🏢 Company-specific assistance
            - Place orders
            - View history
            """)
            if st.button("👤 Customer Login", use_container_width=True, type="primary"):
                st.session_state.mode = "customer"
                st.rerun()
        
        with col_b:
            st.markdown("#### 👨‍💼 Admin Portal")
            st.markdown("""
            - Manage orders
            - View chats
            - User management
            - Knowledge Base
            """)
            if st.button("🔐 Admin Login", use_container_width=True, type="secondary"):
                st.session_state.mode = "admin"
                st.rerun()
    
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #888;'>© 2024 AI Customer Support System. All rights reserved.</div>", unsafe_allow_html=True)

# ========================================
# CUSTOMER MODE
# ========================================
elif st.session_state.mode == "customer":
    
    # Back button in sidebar
    st.sidebar.markdown("### 🏠 Navigation")
    if st.sidebar.button("⬅️ Back to Home"):
        # Reset all states
        st.session_state.mode = None
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.chat_history = []
        st.session_state.show_order_form = False
        st.session_state.first_message = True
        st.session_state.business_details_shown = False
        st.session_state.voice_mode = False
        st.session_state.company_setup_done = False
        st.session_state.company_profile = None
        st.session_state.show_company_setup = False
        st.session_state.last_bot_response = ""
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Company Profile Section
    st.sidebar.markdown("### 🏢 Company Setup")
    
    if st.session_state.company_setup_done and st.session_state.company_profile:
        company_name = st.session_state.company_profile.get("company_name", "Unknown Company")
        st.sidebar.success(f"✅ Active: **{company_name}**")
        
        with st.sidebar.expander("📋 Company Info"):
            st.write(f"**Name:** {company_name}")
            st.write(f"**Tone:** {st.session_state.company_profile.get('tone', 'N/A')}")
            products = st.session_state.company_profile.get('products', [])
            if products:
                st.write(f"**Products:** {', '.join(products[:3])}")
            
            # Show contact info if available
            email = st.session_state.company_profile.get('contact_email', '')
            phone = st.session_state.company_profile.get('contact_phone', '')
            if email:
                st.write(f"**Email:** {email}")
            if phone:
                st.write(f"**Phone:** {phone}")
            
            st.write(f"**Language:** {st.session_state.company_profile.get('lang', 'N/A')}")
        
        if st.sidebar.button("🔄 Change Company"):
            st.session_state.show_company_setup = True
            st.session_state.company_setup_done = False
            st.rerun()
    else:
        st.sidebar.info("💡 Setup a company to get customized support")
        if st.sidebar.button("🏢 Setup Company", use_container_width=True):
            st.session_state.show_company_setup = True
            st.rerun()
    
    st.sidebar.markdown("---")
    
    # Voice Settings
    st.sidebar.markdown("### 🎤 Voice Settings")
    st.session_state.voice_mode = st.sidebar.checkbox(
        "Enable Voice Chat", 
        value=st.session_state.voice_mode,
        help="Enable to use voice input and hear bot responses"
    )
    
    if st.session_state.voice_mode:
        st.sidebar.success("🔊 Voice mode: ON")
        st.session_state.auto_play_response = st.sidebar.checkbox(
            "Auto-play bot responses",
            value=st.session_state.auto_play_response,
            help="Automatically play audio when bot responds"
        )
        st.sidebar.info("💡 Click 🎤 to speak your query!")
    else:
        st.sidebar.info("🔇 Voice mode: OFF")
    
    st.sidebar.markdown("---")
    
    # LOGIN SECTION
    st.sidebar.title("🔐 Customer Login")
    
    if not st.session_state.logged_in:
        with st.sidebar.form("login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔑 Password", type="password")
            login_submit = st.form_submit_button("Login", use_container_width=True)
    
            if login_submit:
                if username and password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.first_message = True
                    st.session_state.business_details_shown = False
                    st.success(f"Welcome, {username}!")
    
                    # Check for existing company profile
                    try:
                        profile_res = requests.get(f"{API_BASE_URL}/get_company_profile/{username}")
                        if profile_res.status_code == 200:
                            data = profile_res.json()
                            if data.get("success") and data.get("profile"):
                                st.session_state.company_profile = data["profile"]
                                st.session_state.company_setup_done = True
                                st.sidebar.success(f"🏢 Loaded profile: {data['profile'].get('company_name', 'Company')}")
                    except:
                        pass
    
                    # Fetch chat history
                    try:
                        res = requests.get(f"{API_BASE_URL}/chat_history/{username}")
                        if res.status_code == 200:
                            data = res.json().get("history", [])
                            st.session_state.chat_history = []
                            for item in data:
                                st.session_state.chat_history.append({"role": "user", "content": item["user"]})
                                st.session_state.chat_history.append({"role": "bot", "content": item["bot"]})
                            
                            if len(st.session_state.chat_history) > 0:
                                st.session_state.first_message = False
                            
                            st.sidebar.success("💬 Chat history loaded!")
                        else:
                            st.sidebar.warning("⚠️ Could not load chat history.")
                    except requests.exceptions.RequestException as e:
                        st.sidebar.error(f"❌ Backend error: {str(e)}")
                    
                    st.rerun()
                else:
                    st.warning("Please fill both fields.")
    else:
        st.sidebar.markdown(f"✅ Logged in as **{st.session_state.username}**")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.chat_history = []
            st.session_state.show_order_form = False
            st.session_state.first_message = True
            st.session_state.business_details_shown = False
            st.session_state.voice_mode = False
            st.session_state.company_setup_done = False
            st.session_state.company_profile = None
            st.session_state.last_bot_response = ""
            st.rerun()
    
    # MAIN PAGE
    st.title("🤖 AI Customer Support Chatbot")
    
    if st.session_state.logged_in:
        
        # COMPANY SETUP FORM
        if st.session_state.show_company_setup:
            st.markdown("---")
            st.markdown("### 🏢 Company Setup")
            st.info("Enter company details to get personalized support with RAG-powered responses!")
            
            with st.form("company_setup_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    company_name = st.text_input(
                        "🏪 Company Name *",
                        placeholder="e.g., TechCorp Inc.",
                        help="Enter the company name"
                    )
                
                with col2:
                    website_url = st.text_input(
                        "🌐 Company Website *",
                        placeholder="https://www.example.com",
                        help="Full website URL including https://"
                    )
                
                st.markdown("**The bot will:**")
                st.markdown("- 🔍 Scrape company information from the website")
                st.markdown("- 📊 Extract and embed content into RAG system")
                st.markdown("- 🎭 Adapt its responses using company context")
                st.markdown("- 💬 Respond with accurate, context-aware answers")
                
                col_submit, col_cancel = st.columns([1, 1])
                
                with col_submit:
                    setup_submit = st.form_submit_button("✅ Setup Company", use_container_width=True)
                
                with col_cancel:
                    setup_cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if setup_submit:
                    if company_name and website_url:
                        with st.spinner("🔍 Fetching and embedding company data... This may take 30-60 seconds."):
                            try:
                                response = requests.post(
                                    f"{API_BASE_URL}/setup_company",
                                    json={
                                        "company_name": company_name,
                                        "website_url": website_url,
                                        "username": st.session_state.username
                                    },
                                    
                                )
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    
                                    if data.get("success"):
                                        st.session_state.company_profile = data["profile"]
                                        st.session_state.company_setup_done = True
                                        st.session_state.show_company_setup = False
                                        
                                        st.success(f"✅ Successfully setup {company_name}!")
                                        
                                        # Show company info
                                        with st.expander("📋 Company Profile", expanded=True):
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                st.write(f"**Company:** {data['profile'].get('company_name', 'N/A')}")
                                                st.write(f"**Tagline:** {data['profile'].get('tagline', 'N/A')}")
                                                st.write(f"**Tone:** {data['profile'].get('tone', 'N/A')}")
                                                
                                                # Contact info
                                                email = data['profile'].get('contact_email', '')
                                                phone = data['profile'].get('contact_phone', '')
                                                if email:
                                                    st.write(f"**Email:** {email}")
                                                if phone:
                                                    st.write(f"**Phone:** {phone}")
                                            
                                            with col2:
                                                st.write(f"**Language:** {data['profile'].get('lang', 'N/A')}")
                                                products = data['profile'].get('products', [])
                                                if products:
                                                    st.write(f"**Products:** {', '.join(products[:5])}")
                                                else:
                                                    st.write("**Products:** N/A")
                                                
                                                # Address
                                                address = data['profile'].get('address', '')
                                                if address:
                                                    st.write(f"**Address:** {address}")
                                            
                                            about = data['profile'].get('short_about', 'N/A')
                                            st.info(f"**About:** {about}")
                                        
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Error: {data.get('error', 'Unknown error')}")
                                        st.info("💡 Tip: Make sure the website URL is correct and accessible.")
                                else:
                                    st.error(f"⚠️ Failed to setup company. Status: {response.status_code}")
                            
                            except requests.exceptions.Timeout:
                                st.error("❌ Request timeout. The website scraping took too long. Please try again.")
                            except requests.exceptions.RequestException as e:
                                st.error(f"❌ Could not connect to backend: {str(e)}")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                    else:
                        st.warning("⚠️ Please fill all required fields (*)")
                
                if setup_cancel:
                    st.session_state.show_company_setup = False
                    st.rerun()
            
            st.markdown("---")
        
        # ORDER FORM
        if st.session_state.show_order_form:
            st.markdown("---")
            st.markdown("### 📦 Order Form")
            st.info("Please fill in your order details below:")
            
            with st.form("order_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    full_name = st.text_input("👤 Full Name *", placeholder="Enter your full name")
                    email = st.text_input("📧 Email Address *", placeholder="your.email@example.com")
                    phone = st.text_input("📱 Phone Number *", placeholder="+92 300 1234567")
                
                with col2:
                    address = st.text_area("🏠 Full Address *", placeholder="Street, Area, City", height=100)
                    house_number = st.text_input("🏡 House/Flat Number", placeholder="House # 123")
                
                product_details = st.text_area("📝 Order Details *", 
                                              placeholder="What would you like to order?", 
                                              height=100)
                
                additional_notes = st.text_area("💬 Additional Notes (Optional)", 
                                               placeholder="Any special instructions?",
                                               height=80)
                
                col_submit, col_cancel = st.columns([1, 1])
                
                with col_submit:
                    submit_order = st.form_submit_button("✅ Submit Order", use_container_width=True)
                
                with col_cancel:
                    cancel_order = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if submit_order:
                    if full_name and email and phone and address and product_details:
                        try:
                            order_data = {
                                "name": full_name,
                                "email": email,
                                "phone": phone,
                                "address": address,
                                "house_number": house_number,
                                "product_details": product_details,
                                "additional_notes": additional_notes,
                                "username": st.session_state.username
                            }
                            
                            response = requests.post(
                                f"{API_BASE_URL}/order",
                                json=order_data,
                                
                            )
                            
                            if response.status_code == 200:
                                st.success("✅ Order submitted successfully! We'll contact you soon.")
                                
                                bot_message = f"Thank you {full_name}! Your order has been received. We will contact you at {phone} shortly. 🎉"
                                st.session_state.chat_history.append({"role": "bot", "content": bot_message})
                                st.session_state.last_bot_response = bot_message
                                
                                st.session_state.show_order_form = False
                                st.rerun()
                            else:
                                st.error("⚠️ Failed to submit order. Please try again.")
                        
                        except requests.exceptions.RequestException:
                            st.error("❌ Could not connect to backend. Please try again.")
                    else:
                        st.warning("⚠️ Please fill all required fields (*)")
                
                if cancel_order:
                    st.session_state.show_order_form = False
                    st.rerun()
            
            st.markdown("---")
        
        # CHAT WINDOW
        st.subheader("💬 Chat Window")
        
        # Show company context indicator
        if st.session_state.company_setup_done and st.session_state.company_profile:
            company_name = st.session_state.company_profile.get("company_name", "Company")
            st.info(f"🏢 Currently assisting you as **{company_name}** support representative (RAG-powered)")
    
        # Display chat history
        for i, chat in enumerate(st.session_state.chat_history):
            if chat["role"] == "user":
                message(chat["content"], is_user=True, key=f"user_{i}")
            else:
                message(chat["content"], key=f"bot_{i}")
                
                # Add listen button for each bot message in voice mode
                if st.session_state.voice_mode:
                    if st.button(f"🔊 Listen", key=f"listen_{i}"):
                        with st.spinner("🎵 Generating audio..."):
                            audio_file = text_to_speech(chat["content"])
                            if audio_file:
                                play_audio(audio_file)
                                st.success("▶️ Playing...")
    
        st.markdown("---")
        
        # INPUT SECTION
        user_input = st.text_input("Type your message:", key="input", placeholder="Ask something...")
    
        # Button layout
        if st.session_state.voice_mode:
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        else:
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            col5 = None
        
        with col1:
            send = st.button("🚀 Send", use_container_width=True)
        
        with col2:
            if st.session_state.voice_mode:
                voice_btn = st.button("🎤 Voice", use_container_width=True)
            else:
                voice_btn = False
        
        with col3:
            new_chat = st.button("🆕 New Chat", use_container_width=True)
        
        with col4:
            reset = st.button("🔁 Reset", use_container_width=True)
        
        if col5:
            with col5:
                if st.session_state.last_bot_response:
                    repeat_btn = st.button("🔊 Repeat", use_container_width=True)
                else:
                    repeat_btn = False
        else:
            repeat_btn = False
    
        # VOICE INPUT
        if voice_btn and st.session_state.voice_mode:
            voice_text = speech_to_text()
            
            if voice_text and not voice_text.startswith("❌") and not voice_text.startswith("⏱️"):
                st.success(f"📝 You said: **{voice_text}**")
                user_input = voice_text
                send = True
            else:
                st.error(voice_text)
    
        # SEND MESSAGE
        if send and user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
    
            # Check for order intent
            if detect_order_intent(user_input) and st.session_state.business_details_shown:
                business_info = get_business_details()
                bot_reply = f"{business_info}\n\n✅ Great! Please fill out the order form below to proceed with your order. 📦"
                st.session_state.show_order_form = True
                st.session_state.business_details_shown = False
            
            # First message - show business details
            elif st.session_state.first_message:
                try:
                    with st.spinner("🤖 Thinking (using Ollama + RAG)..."):
                        payload = {
                            "query": user_input,
                            "username": st.session_state.username
                        }
                        
                        # Add company profile if available
                        if st.session_state.company_profile:
                            payload["company_profile"] = st.session_state.company_profile
                        
                        response = requests.post(
                            f"{API_BASE_URL}/chat",
                            json=payload,
                              # Increased to 2 minutes for Ollama
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            ai_response = data.get("response", "")
                            kb_context = data.get("kb_context", [])
                            
                            business_info = get_business_details()
                            
                            bot_reply = f"{ai_response}\n\n---\n\n{business_info}\n\n---\n\n"
                            
                            if kb_context:
                                st.info(f"📚 Retrieved {len(kb_context)} relevant context(s) from knowledge base")
                            
                            st.session_state.first_message = False
                            st.session_state.business_details_shown = True
                        else:
                            bot_reply = f"⚠️ Error {response.status_code}: Could not get response"
                            
                except requests.exceptions.Timeout:
                    bot_reply = "❌ Request timeout. The AI is taking too long to respond. Please try again."
                except requests.exceptions.RequestException as e:
                    bot_reply = f"❌ Backend connection error: {str(e)}"
                except Exception as e:
                    bot_reply = f"❌ Error: {str(e)}"
            
            # Subsequent messages
            else:
                try:
                    with st.spinner("🤖 Thinking (using Ollama + RAG)..."):
                        payload = {
                            "query": user_input,
                            "username": st.session_state.username
                        }
                        
                        # Add company profile if available
                        if st.session_state.company_profile:
                            payload["company_profile"] = st.session_state.company_profile
                        
                        response = requests.post(
                            f"{API_BASE_URL}/chat",
                            json=payload,
                            
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            ai_response = data.get("response", "Hmm... I couldn't understand that.")
                            kb_context = data.get("kb_context", [])
                            
                            bot_reply = f"{ai_response}\n\n---\n"
                            
                            if kb_context:
                                with st.expander("📚 View Retrieved Context"):
                                    for idx, ctx in enumerate(kb_context, 1):
                                        st.markdown(f"**Context {idx}:**")
                                        st.text(ctx[:200] + "..." if len(ctx) > 200 else ctx)
                            
                            st.session_state.business_details_shown = True
                        else:
                            bot_reply = f"⚠️ Error {response.status_code}: Could not get response"
                            
                except requests.exceptions.Timeout:
                    bot_reply = "❌ Request timeout. The AI is taking too long to respond. Please try again."
                except requests.exceptions.RequestException as e:
                    bot_reply = f"❌ Backend connection error: {str(e)}"
                except Exception as e:
                    bot_reply = f"❌ Error: {str(e)}"
    
            st.session_state.chat_history.append({"role": "bot", "content": bot_reply})
            st.session_state.last_bot_response = bot_reply
            
            # Auto-play voice response if enabled
            if st.session_state.voice_mode and st.session_state.auto_play_response:
                with st.spinner("🎵 Generating audio..."):
                    audio_file = text_to_speech(bot_reply)
                    if audio_file:
                        play_audio(audio_file)
    
            st.rerun()
        
        # Repeat last response
        if repeat_btn and st.session_state.last_bot_response:
            with st.spinner("🎵 Generating audio..."):
                audio_file = text_to_speech(st.session_state.last_bot_response)
                if audio_file:
                    play_audio(audio_file)
                    st.success("▶️ Playing...")
    
        # New chat
        if new_chat:
            st.session_state.chat_history = []
            st.session_state.show_order_form = False
            st.session_state.first_message = True
            st.session_state.business_details_shown = False
            st.session_state.last_bot_response = ""
            st.success("🆕 New chat started!")
            st.rerun()
    
        # Reset
        if reset:
            st.session_state.chat_history = []
            st.session_state.show_order_form = False
            st.session_state.first_message = True
            st.session_state.business_details_shown = False
            st.session_state.last_bot_response = ""
            st.rerun()
    else:
        st.warning("⚠️ Please login to start chatting!")
        st.info("👈 Use the sidebar to login")

# ========================================
# ADMIN MODE
# ========================================
elif st.session_state.mode == "admin":
    st.sidebar.markdown("### 🏠 Navigation")
    if st.sidebar.button("⬅️ Back to Home"):
        st.session_state.mode = None
        st.session_state.admin_logged_in = False
        st.rerun()
    
    st.title("👨‍💼 Admin Portal")
    
    if not st.session_state.admin_logged_in:
        st.markdown("### 🔐 Admin Login")
        st.info("Please login with admin credentials to access the dashboard")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("admin_login_form"):
                admin_user = st.text_input("👤 Username")
                admin_pass = st.text_input("🔑 Password", type="password")
                admin_login_btn = st.form_submit_button("🔓 Login", use_container_width=True)
                
                if admin_login_btn:
                    if admin_user == ADMIN_USERNAME and admin_pass == ADMIN_PASSWORD:
                        st.session_state.admin_logged_in = True
                        st.success("✅ Admin login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials!")
    else:
        st.success(f"✅ Logged in as Admin")
        
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.rerun()
        
        with col2:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        
        # Admin Dashboard
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📦 Orders", "💬 Chats", "📚 Knowledge Base", "⚙️ System"])
        
        with tab1:
            st.subheader("📊 Analytics Dashboard")
            
            col1, col2, col3, col4 = st.columns(4)
            
            try:
                # Fetch stats
                orders_res = requests.get(f"{API_BASE_URL}/orders")
                kb_stats_res = requests.get(f"{API_BASE_URL}/kb_stats")
                
                total_orders = len(orders_res.json().get("orders", [])) if orders_res.status_code == 200 else 0
                kb_stats = kb_stats_res.json() if kb_stats_res.status_code == 200 else {}
                
                with col1:
                    st.metric("📦 Total Orders", total_orders)
                
                with col2:
                    st.metric("📚 KB Entries", kb_stats.get("total_entries", 0))
                
                with col3:
                    st.metric("🔍 RAG Vectors", kb_stats.get("rag_vectors", 0))
                
                with col4:
                    st.metric("🤖 AI Model", "Ollama", delta="Active")
                
                st.markdown("---")
                
                # Recent activity
                st.markdown("#### 📈 Recent Activity")
                
                if orders_res.status_code == 200:
                    orders = orders_res.json().get("orders", [])
                    if orders:
                        recent_orders = orders[:5]  # First 5 orders
                        st.markdown("**Recent Orders:**")
                        for order in recent_orders:
                            st.write(f"- **{order.get('name', 'N/A')}** - {order.get('product_details', 'N/A')[:50]}...")
                    else:
                        st.info("No orders yet")
                
                # KB Stats
                if kb_stats:
                    st.markdown("---")
                    st.markdown("#### 📚 Knowledge Base Statistics")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Total Entries:** {kb_stats.get('total_entries', 0)}")
                        st.write(f"**RAG Vectors:** {kb_stats.get('rag_vectors', 0)}")
                    with col2:
                        st.write(f"**Embedding Model:** {kb_stats.get('embedding_model', 'N/A')}")
                        st.write(f"**Index Type:** FAISS")
                
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Unable to fetch dashboard data: {str(e)}")
        
        with tab2:
            st.subheader("📦 Order Management")
            
            try:
                response = requests.get(f"{API_BASE_URL}/orders")
                if response.status_code == 200:
                    orders = response.json().get("orders", [])
                    if orders:
                        df = pd.DataFrame(orders)
                        
                        # Add filters
                        st.markdown("#### 🔍 Filters")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            search_name = st.text_input("Search by name", "")
                        
                        with col2:
                            search_username = st.text_input("Search by username", "")
                        
                        # Apply filters
                        if search_name:
                            df = df[df['name'].str.contains(search_name, case=False, na=False)]
                        
                        if search_username and 'username' in df.columns:
                            df = df[df['username'].str.contains(search_username, case=False, na=False)]
                        
                        st.markdown(f"**Showing {len(df)} orders**")
                        st.dataframe(df, use_container_width=True)
                        
                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Orders CSV",
                            data=csv,
                            file_name=f"orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.info("📭 No orders found.")
                else:
                    st.error("⚠️ Failed to fetch orders.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Backend not reachable: {str(e)}")
        
        with tab3:
            st.subheader("💬 Chat History Management")
            
            st.info("💡 Chat history is stored in the database. View individual user history by username.")
            
            username_search = st.text_input("Enter username to view chat history:", "")
            
            if username_search:
                try:
                    response = requests.get(f"{API_BASE_URL}/chat_history/{username_search}")
                    if response.status_code == 200:
                        history = response.json().get("history", [])
                        if history:
                            st.success(f"Found {len(history)} messages for **{username_search}**")
                            
                            for idx, chat in enumerate(history, 1):
                                with st.expander(f"Message {idx}"):
                                    st.markdown(f"**User:** {chat['user']}")
                                    st.markdown(f"**Bot:** {chat['bot']}")
                        else:
                            st.info(f"No chat history found for {username_search}")
                    else:
                        st.error("Failed to fetch chat history")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Backend error: {str(e)}")
        
        with tab4:
            st.subheader("📚 Knowledge Base Management")
            
            # Add new knowledge
            st.markdown("#### ➕ Add New Knowledge")
            with st.form("add_kb_form"):
                kb_text = st.text_area("Knowledge Text", placeholder="Enter knowledge base content...", height=150)
                submit_kb = st.form_submit_button("💾 Add to Knowledge Base", use_container_width=True)
                
                if submit_kb and kb_text:
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/add_kb",
                            data={"text": kb_text},
                            
                        )
                        if response.status_code == 200:
                            st.success("✅ Knowledge added successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to add knowledge")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Error: {str(e)}")
            
            st.markdown("---")
            
            # KB Stats
            try:
                response = requests.get(f"{API_BASE_URL}/kb_stats")
                if response.status_code == 200:
                    stats = response.json()
                    st.markdown("#### 📊 Knowledge Base Statistics")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Entries", stats.get("total_entries", 0))
                    with col2:
                        st.metric("RAG Vectors", stats.get("rag_vectors", 0))
                    with col3:
                        st.metric("Embedding Dims", stats.get("embedding_dimensions", 384))
                    
                    st.info(f"**Embedding Model:** {stats.get('embedding_model', 'N/A')}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error fetching KB stats: {str(e)}")
        
        with tab5:
            st.subheader("⚙️ System Information")
            
            try:
                # Backend health check
                response = requests.get(f"{API_BASE_URL}/")
                if response.status_code == 200:
                    st.success("✅ Backend API is running")
                    data = response.json()
                    st.json(data)
                else:
                    st.error("⚠️ Backend API returned unexpected status")
            except:
                st.error("❌ Backend API is not reachable")
            
            st.markdown("---")
            
            st.markdown("#### 🔧 System Components")
            components = {
                "Backend": "FastAPI",
                "Database": "PostgreSQL",
                "AI Model": "Ollama (gemma3:1b)",
                "RAG": "FAISS + Sentence Transformers",
                "Embeddings": "all-MiniLM-L6-v2",
                "Frontend": "Streamlit"
            }
            
            for key, value in components.items():
                st.write(f"**{key}:** {value}")
            
            st.markdown("---")
            st.markdown("#### 📊 API Endpoints")
            endpoints = [
                "/chat - Chat with AI",
                "/setup_company - Setup company profile",
                "/order - Place order",
                "/chat_history/{username} - Get chat history",
                "/orders - Get all orders",
                "/add_kb - Add knowledge",
                "/kb_stats - KB statistics"
            ]
            for endpoint in endpoints:
                st.code(endpoint)
        
        st.markdown("---")
        st.markdown("<div style='text-align: center; color: #888;'>Admin Portal - Advanced AI Customer Support System</div>", unsafe_allow_html=True)