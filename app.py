import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from PIL import Image
from backend import (
    extract_pdf_text, 
    calculate_ats_score, 
    save_participant_application,
    get_leaderboard,
    get_competition_stats,
    register_participant,
    check_participant_exists,
    get_participant_upload_count,
    get_participant_scores
)

# Page config
st.set_page_config(
    page_title="MLSC Competition Portal",
    page_icon="mlsc.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'registered' not in st.session_state:
    st.session_state.registered = False
if 'participant_id' not in st.session_state:
    st.session_state.participant_id = None
if 'participant_data' not in st.session_state:
    st.session_state.participant_data = {}
if 'show_confetti' not in st.session_state:
    st.session_state.show_confetti = False

# Enhanced Custom CSS with Modern Design
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main Background with animated gradient */
    .main {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        background-size: 200% 200%;
        animation: gradientShift 15s ease infinite;
        background-attachment: fixed;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .stApp {
        background: transparent;
    }
    
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 0rem;
        max-width: 1400px;
    }
    
    /* Enhanced Logo Header */
    .logo-header {
        display: flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.98);
        padding: 24px 35px;
        border-radius: 24px;
        margin-bottom: 35px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.25),
                    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
        backdrop-filter: blur(20px);
        position: relative;
        overflow: hidden;
    }
    
    .logo-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(91, 192, 222, 0.1), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .logo-img {
        width: 60px;
        height: 60px;
        margin-right: 20px;
        filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
    }
    
    .logo-title {
        background: linear-gradient(135deg, #0f2027 0%, #2c5364 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.9rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    /* Premium Glass Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.97);
        backdrop-filter: blur(20px) saturate(180%);
        padding: 45px;
        border-radius: 28px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12),
                    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
        border: 1px solid rgba(255, 255, 255, 0.6);
        margin-bottom: 28px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.18);
    }
    
    .glass-card-dark {
        background: linear-gradient(135deg, 
            rgba(15, 32, 39, 0.95) 0%, 
            rgba(44, 83, 100, 0.95) 100%);
        backdrop-filter: blur(20px) saturate(180%);
        padding: 45px;
        border-radius: 28px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4),
                    0 0 0 1px rgba(91, 192, 222, 0.2) inset;
        border: 1px solid rgba(91, 192, 222, 0.25);
        color: white;
        margin-bottom: 28px;
    }
    
    /* Registration Container Enhancement */
    .register-container {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(30px) saturate(180%);
        padding: 55px;
        border-radius: 32px;
        box-shadow: 0 20px 80px rgba(0, 0, 0, 0.3),
                    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
        border: 2px solid rgba(91, 192, 222, 0.3);
        max-width: 540px;
        margin: 70px auto;
    }
    
    .register-title {
        background: linear-gradient(135deg, #0f2027 0%, #2c5364 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 14px;
        text-align: center;
        letter-spacing: -0.5px;
    }
    
    .register-subtitle {
        color: #5BC0DE;
        text-align: center;
        margin-bottom: 45px;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    /* Enhanced Card Headers */
    .card-header {
        background: linear-gradient(135deg, #0f2027 0%, #2c5364 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.9rem;
        font-weight: 800;
        margin-bottom: 35px;
        padding-bottom: 22px;
        border-bottom: 4px solid #5BC0DE;
        letter-spacing: -0.5px;
        position: relative;
    }
    
    .card-header::after {
        content: '';
        position: absolute;
        bottom: -4px;
        left: 0;
        width: 60px;
        height: 4px;
        background: linear-gradient(90deg, #5BC0DE, transparent);
    }
    
    /* Stunning Score Display */
    .score-display {
        text-align: center;
        padding: 70px 45px;
        background: linear-gradient(135deg, #0f2027 0%, #2c5364 50%, #5BC0DE 100%);
        border-radius: 32px;
        color: white;
        margin: 35px 0;
        box-shadow: 0 20px 60px rgba(15, 32, 39, 0.5),
                    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
        position: relative;
        overflow: hidden;
    }
    
    .score-display::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(91, 192, 222, 0.3) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1) rotate(0deg); opacity: 0.4; }
        50% { transform: scale(1.15) rotate(180deg); opacity: 0.7; }
    }
    
    .score-number {
        font-size: 7rem;
        font-weight: 900;
        margin: 0;
        text-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        position: relative;
        z-index: 1;
        letter-spacing: -3px;
    }
    
    .score-label {
        font-size: 1.7rem;
        opacity: 0.95;
        margin-top: 24px;
        font-weight: 700;
        position: relative;
        z-index: 1;
        letter-spacing: 0.5px;
    }
    
    /* Enhanced Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.98) 0%, 
            rgba(240, 240, 245, 0.98) 100%);
        backdrop-filter: blur(15px);
        padding: 40px 28px;
        border-radius: 24px;
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.12),
                    0 0 0 1px rgba(91, 192, 222, 0.1) inset;
        border-top: 6px solid #5BC0DE;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, transparent, rgba(91, 192, 222, 0.05));
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-10px) scale(1.02);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
        border-top-color: #0f2027;
    }
    
    .metric-card:hover::before {
        opacity: 1;
    }
    
    .metric-value {
        font-size: 3.2rem;
        font-weight: 900;
        background: linear-gradient(135deg, #0f2027 0%, #2c5364 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 18px 0;
        letter-spacing: -1px;
    }
    
    .metric-label {
        color: #5BC0DE;
        font-size: 1.05rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 800;
    }
    
    /* Enhanced Leaderboard */
    .leaderboard-rank {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 65px;
        height: 65px;
        background: linear-gradient(135deg, #0f2027 0%, #2c5364 100%);
        color: white;
        border-radius: 50%;
        font-weight: 900;
        font-size: 1.5rem;
        margin-right: 24px;
        box-shadow: 0 6px 24px rgba(15, 32, 39, 0.5);
        position: relative;
    }
    
    .leaderboard-rank::after {
        content: '';
        position: absolute;
        inset: -3px;
        border-radius: 50%;
        background: linear-gradient(135deg, #5BC0DE, #0f2027);
        z-index: -1;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .leaderboard-item:hover .leaderboard-rank::after {
        opacity: 1;
    }
    
    .leaderboard-item {
        background: linear-gradient(135deg, 
            rgba(255, 255, 255, 0.97) 0%, 
            rgba(240, 240, 245, 0.97) 100%);
        backdrop-filter: blur(15px);
        padding: 28px;
        border-radius: 20px;
        margin: 20px 0;
        border-left: 7px solid #5BC0DE;
        display: flex;
        align-items: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
        position: relative;
        overflow: hidden;
    }
    
    .leaderboard-item::before {
        content: '';
        position: absolute;
        left: -100%;
        top: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(91, 192, 222, 0.1), transparent);
        transition: left 0.5s ease;
    }
    
    .leaderboard-item:hover {
        transform: translateX(12px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.16);
        border-left-color: #0f2027;
    }
    
    .leaderboard-item:hover::before {
        left: 100%;
    }
    
    .top-badge {
        background: linear-gradient(135deg, #5BC0DE 0%, #2c5364 100%);
        color: white;
        padding: 12px 28px;
        border-radius: 28px;
        font-weight: 800;
        font-size: 0.95rem;
        box-shadow: 0 5px 18px rgba(91, 192, 222, 0.5);
        letter-spacing: 0.5px;
    }
    
    /* Enhanced Limit Badges */
    .limit-badge {
        display: inline-block;
        padding: 14px 28px;
        background: linear-gradient(135deg, 
            rgba(91, 192, 222, 0.15) 0%, 
            rgba(44, 83, 100, 0.15) 100%);
        border: 2px solid #5BC0DE;
        border-radius: 28px;
        color: #0f2027;
        font-weight: 800;
        font-size: 1.05rem;
        margin: 14px 10px;
        box-shadow: 0 5px 18px rgba(91, 192, 222, 0.25);
        transition: all 0.3s ease;
    }
    
    .limit-badge:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 24px rgba(91, 192, 222, 0.35);
    }
    
    .limit-warning {
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.2) 0%, rgba(255, 152, 0, 0.2) 100%);
        border-color: #ffc107;
        color: #ff6f00;
    }
    
    .limit-danger {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.2) 0%, rgba(211, 47, 47, 0.2) 100%);
        border-color: #f44336;
        color: #c62828;
    }
    
    /* Premium Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #5BC0DE 0%, #2c5364 100%);
        color: white;
        border: none;
        padding: 18px 45px;
        border-radius: 50px;
        font-weight: 800;
        font-size: 1.1rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 10px 30px rgba(91, 192, 222, 0.4);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        position: relative;
        overflow: hidden;
    }
    
    .stButton>button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        transform: translate(-50%, -50%);
        transition: width 0.6s ease, height 0.6s ease;
    }
    
    .stButton>button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton>button:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 45px rgba(91, 192, 222, 0.6);
        background: linear-gradient(135deg, #2c5364 0%, #0f2027 100%);
    }
    
    .stButton>button:disabled {
        background: linear-gradient(135deg, #E6E4E6 0%, #cccccc 100%);
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }
    
    /* Enhanced Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(135deg, #5BC0DE 0%, #2c5364 100%);
        height: 8px;
        border-radius: 10px;
    }
    
    /* Premium Input Fields */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        border-radius: 14px;
        border: 2px solid rgba(91, 192, 222, 0.3);
        padding: 16px;
        font-size: 1.05rem;
        transition: all 0.3s ease;
        background: rgba(255, 255, 255, 0.95);
    }
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #5BC0DE;
        box-shadow: 0 0 0 4px rgba(91, 192, 222, 0.15);
        background: white;
    }
    
    /* Enhanced File Uploader */
    .stFileUploader {
        background: linear-gradient(135deg, rgba(91, 192, 222, 0.08), rgba(44, 83, 100, 0.08));
        border-radius: 18px;
        border: 3px dashed #5BC0DE;
        padding: 30px;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        background: linear-gradient(135deg, rgba(91, 192, 222, 0.12), rgba(44, 83, 100, 0.12));
        border-color: #2c5364;
    }
    
    /* Enhanced Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2027 0%, #2c5364 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Enhanced Competition Banner */
    .competition-banner {
        background: linear-gradient(135deg, #0f2027 0%, #2c5364 50%, #5BC0DE 100%);
        color: white;
        padding: 55px 40px;
        border-radius: 32px;
        text-align: center;
        margin-bottom: 45px;
        box-shadow: 0 20px 60px rgba(15, 32, 39, 0.4);
        position: relative;
        overflow: hidden;
    }
    
    .competition-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.12) 0%, transparent 70%);
        animation: rotate 25s linear infinite;
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Enhanced Skill Tags */
    .skill-tag {
        display: inline-block;
        padding: 12px 24px;
        background: linear-gradient(135deg, #5BC0DE 0%, #2c5364 100%);
        color: white;
        border-radius: 28px;
        margin: 10px;
        font-weight: 700;
        font-size: 0.95rem;
        box-shadow: 0 5px 18px rgba(91, 192, 222, 0.35);
        transition: all 0.3s ease;
    }
    
    .skill-tag:hover {
        transform: translateY(-4px) scale(1.05);
        box-shadow: 0 8px 24px rgba(91, 192, 222, 0.5);
    }
    
    /* Enhanced Messages */
    .stSuccess {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.15) 0%, rgba(56, 142, 60, 0.15) 100%);
        border: 2px solid #4caf50;
        border-radius: 14px;
        color: #2e7d32;
        padding: 16px;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.15) 0%, rgba(211, 47, 47, 0.15) 100%);
        border: 2px solid #f44336;
        border-radius: 14px;
        color: #c62828;
        padding: 16px;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.15) 0%, rgba(255, 152, 0, 0.15) 100%);
        border: 2px solid #ffc107;
        border-radius: 14px;
        color: #ff6f00;
        padding: 16px;
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(91, 192, 222, 0.15) 0%, rgba(44, 83, 100, 0.15) 100%);
        border: 2px solid #5BC0DE;
        border-radius: 14px;
        color: #2c5364;
        padding: 16px;
    }
    
    /* Info Box Enhancement */
    .info-box {
        background: linear-gradient(135deg, rgba(91, 192, 222, 0.12) 0%, rgba(44, 83, 100, 0.12) 100%);
        backdrop-filter: blur(10px);
        padding: 35px;
        border-radius: 20px;
        border-left: 7px solid #5BC0DE;
        margin: 28px 0;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.1);
    }
    
    /* Tabs Enhancement */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #5BC0DE 0%, #2c5364 100%);
        color: white;
    }
    
    /* Spinner Enhancement */
    .stSpinner > div {
        border-top-color: #5BC0DE !important;
    }
    </style>
""", unsafe_allow_html=True)

# Logo Header Function
def show_logo_header(title):
    try:
        logo = Image.open("mlsc.png")
        st.markdown('<div class="logo-header">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 15])
        with col1:
            st.image(logo, width=60)
        with col2:
            st.markdown(f"<div class='logo-title'>{title}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except:
        st.markdown(f"<div class='logo-header'><div class='logo-title'>{title}</div></div>", unsafe_allow_html=True)

# REGISTRATION PAGE
if not st.session_state.registered:
    # Centered logo
    try:
        logo = Image.open("mlsc.png")
        left_spacer, center, right_spacer = st.columns([1, 1, 1])
        with center:
            st.image(logo, width=200)
    except:
        pass
    
    st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.95); font-size: 1.3rem; font-weight: 600;'>Microsoft Learn Student Chapter @ TIET</p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="competition-banner">
            <h1 style='color: white; margin: 0; font-size: 3rem; position: relative; z-index: 1; text-shadow: 0 5px 25px rgba(0,0,0,0.4); letter-spacing: -1px;'>PERFECT CV MATCH 2025</h1>
            <p style='margin: 18px 0 0 0; font-size: 1.3rem; opacity: 0.95; position: relative; z-index: 1; font-weight: 600;'>Microsoft Learn Student Chapter @ TIET</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="register-title">Participant Registration</div>', unsafe_allow_html=True)
        st.markdown('<div class="register-subtitle">Join the competition and showcase your skills</div>', unsafe_allow_html=True)
        
        with st.form("registration_form", clear_on_submit=False):
            name = st.text_input(
                "Full Name",
                placeholder="Enter your complete name",
                help="Your name as per university records"
            )
            
            email = st.text_input(
                "Email Address",
                placeholder="student@thapar.edu",
                help="Your institutional email address"
            )
            
            mobile = st.text_input(
                "Mobile Number",
                placeholder="+91 XXXXX XXXXX",
                help="10-digit mobile number"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("🚀 Register & Start Competing", use_container_width=True)
            
            if submit:
                errors = []
                if not name or len(name) < 3:
                    errors.append("Name must be at least 3 characters")
                if not email or '@' not in email or '@thapar.edu' not in email.lower():
                    errors.append("Valid Thapar email required (e.g., @thapar.edu)")
                if not mobile or len(mobile.replace('+', '').replace(' ', '').replace('-', '')) < 10:
                    errors.append("Valid mobile number required")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    with st.spinner("🔄 Registering participant..."):
                        time.sleep(0.8)
                        
                        existing = check_participant_exists(email)
                        
                        if existing:
                            participant_id = existing['id']
                            st.info("👋 Welcome back! You are already registered.")
                        else:
                            participant_id = register_participant(name, email, mobile)
                            st.success("✅ Registration Successful!")
                        
                        st.session_state.registered = True
                        st.session_state.participant_id = participant_id
                        st.session_state.participant_data = {
                            'name': name,
                            'email': email,
                            'mobile': mobile
                        }
                        
                        time.sleep(1)
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Competition Info
        st.markdown("""
        <div class="info-box">
            <h4 style='color: #2c5364; margin-top: 0; font-weight: 800; font-size: 1.2rem;'>📋 Competition Rules</h4>
            <ul style='color: #0f2027; line-height: 2.2; font-weight: 600;'>
                <li><strong>Maximum 5 resume uploads</strong> per participant</li>
                <li><strong>Unlimited score views</strong> - check anytime!</li>
                <li>Upload PDF format only (max 20MB)</li>
                <li>Top 10 scorers featured on leaderboard</li>
                <li>Privacy protected - only scores are public</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# MAIN APPLICATION
else:
    upload_count = get_participant_upload_count(st.session_state.participant_id)
    MAX_UPLOADS = 5
    
    # Sidebar
    with st.sidebar:
        try:
            logo = Image.open("mlsc.png")
            st.image(logo, width=140)
        except:
            pass
        
        st.markdown("---")
        st.markdown("### 👤 Participant Profile")
        st.write(f"**{st.session_state.participant_data['name']}**")
        st.write(f"📧 {st.session_state.participant_data['email']}")
        st.write(f"🆔 {st.session_state.participant_id[:8]}...")
        
        st.markdown("---")
        st.markdown("### 📊 Upload Status")
        
        upload_remaining = MAX_UPLOADS - upload_count
        progress_value = upload_count / MAX_UPLOADS
        
        st.progress(progress_value)
        
        if upload_remaining > 1:
            badge_class = "limit-badge"
        elif upload_remaining == 1:
            badge_class = "limit-badge limit-warning"
        else:
            badge_class = "limit-badge limit-danger"
        
        st.markdown(f"<div class='{badge_class}'>{upload_count}/{MAX_UPLOADS} Uploads Used</div>", unsafe_allow_html=True)
        
        if upload_remaining > 0:
            st.success(f"✅ {upload_remaining} remaining")
        else:
            st.error("⚠️ Limit reached")
        
        st.markdown("---")
        st.markdown("### 🧭 Navigation")
        page = st.radio(
            "",
            ["📤 Submit Application", "📈 My Scores", "🏆 Leaderboard", "📊 Competition Stats"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        if st.button("🚪 Exit Competition", use_container_width=True):
            st.session_state.registered = False
            st.session_state.participant_id = None
            st.session_state.participant_data = {}
            st.rerun()
    
    # PAGE 1: Submit Application
    if page == "📤 Submit Application":
        show_logo_header("Submit Your Resume")
        
        if upload_count >= MAX_UPLOADS:
            st.markdown("""
                
                    <h2 style='color: white; text-align: center; font-size: 2rem;'>⛔ Upload Limit Reached</h2>
                    <p style='text-align: center; font-size: 1.2rem; opacity: 0.9; margin-top: 20px;'>
                        You have used all 5 uploads. View your scores in 'My Scores' section.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            st.stop()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('')
            st.markdown('<div class="card-header">📄 Resume Submission</div>', unsafe_allow_html=True)
            
            uploads_left = MAX_UPLOADS - upload_count
            if uploads_left <= 2:
                st.warning(f"⚠️ Only {uploads_left} upload(s) remaining!")
            else:
                st.info(f"ℹ️ {uploads_left} of {MAX_UPLOADS} uploads remaining")
            
            uploaded_file = st.file_uploader(
                "Upload Your Resume (PDF)",
                type=['pdf'],
                help="Maximum file size: 20MB"
            )
            
            job_description = st.text_area(
                "Target Job Description",
                height=280,
                placeholder="Paste the job description you're targeting...\n\nExample:\nWe are looking for a Software Developer with 3+ years of experience...",
                help="Paste the complete job description"
            )
            
            if st.button("🚀 Submit & Calculate Score", type="primary", use_container_width=True, disabled=(upload_count >= MAX_UPLOADS)):
                if uploaded_file and job_description:
                    try:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("📄 Reading your resume...")
                        progress_bar.progress(20)
                        time.sleep(0.5)
                        text = extract_pdf_text(uploaded_file)
                        
                        status_text.text("🤖 Analyzing with AI engine...")
                        progress_bar.progress(50)
                        time.sleep(0.7)
                        result = calculate_ats_score(text, job_description)
                        
                        status_text.text("💾 Saving results...")
                        progress_bar.progress(80)
                        time.sleep(0.5)
                        
                        save_participant_application(
                            result['score'],
                            result['skills'],
                            result['experience_years'],
                            st.session_state.participant_id
                        )
                        
                        progress_bar.progress(100)
                        time.sleep(0.4)
                        progress_bar.empty()
                        status_text.empty()
                        
                        st.success(f"✅ Submission {upload_count + 1}/{MAX_UPLOADS} successful!")
                        
                        # Score Display
                        score = result['score']
                        if score >= 80:
                            verdict = "🎉 Excellent Match"
                            emoji = "🌟"
                        elif score >= 60:
                            verdict = "👍 Good Match"
                            emoji = "✨"
                        else:
                            verdict = "📈 Needs Improvement"
                            emoji = "💪"
                        
                        st.markdown(f"""
                            <div class="score-display">
                                <div style="font-size: 3rem; position: relative; z-index: 1; margin-bottom: 10px;">{emoji}</div>
                                <div class="score-number">{score:.1f}%</div>
                                <div class="score-label">{verdict}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Gauge Chart
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number+delta",
                            value=score,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={'text': "Match Score", 'font': {'size': 26, 'color': '#0f2027', 'family': 'Inter', 'weight': 800}},
                            delta={'reference': 70, 'increasing': {'color': '#4caf50'}},
                            gauge={
                                'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': '#0f2027'},
                                'bar': {'color': "#5BC0DE", 'thickness': 0.75},
                                'steps': [
                                    {'range': [0, 60], 'color': "rgba(244, 67, 54, 0.15)"},
                                    {'range': [60, 80], 'color': "rgba(255, 193, 7, 0.15)"},
                                    {'range': [80, 100], 'color': "rgba(76, 175, 80, 0.15)"}
                                ],
                                'threshold': {
                                    'line': {'color': "#2c5364", 'width': 6},
                                    'thickness': 0.85,
                                    'value': 85
                                }
                            }
                        ))
                        fig.update_layout(
                            height=400,
                            margin=dict(l=20, r=20, t=80, b=20),
                            paper_bgcolor='rgba(0,0,0,0)',
                            font={'color': '#0f2027', 'family': 'Inter', 'size': 14}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Analysis
                        st.markdown("### 🔍 Analysis Summary")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            skill_delta = "High" if len(result['skills']) >= 5 else "Low"
                            st.metric("Skills Detected", f"{len(result['skills'])} skills", 
                                     delta=skill_delta, delta_color="normal" if skill_delta == "High" else "inverse")
                        with col_b:
                            exp_delta = "Strong" if result['experience_years'] >= 3 else "Entry"
                            st.metric("Experience", f"{result['experience_years']} years",
                                     delta=exp_delta, delta_color="normal" if exp_delta == "Strong" else "off")
                        
                        if result['skills']:
                            st.markdown("### 🎯 Detected Skills")
                            skills_html = "".join([
                                f'<span class="skill-tag">{skill}</span>'
                                for skill in result['skills']
                            ])
                            st.markdown(f'<div style="text-align: center; margin-top: 20px;">{skills_html}</div>', unsafe_allow_html=True)
                        
                        time.sleep(1.5)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ Please upload resume and enter job description")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('')
            st.markdown('<h3 style="color: white; border-bottom: 4px solid #5BC0DE; padding-bottom: 18px; font-weight: 800;">💡 Guidelines</h3>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='color: white; line-height: 2;'>
            <p style='font-size: 1.1rem; font-weight: 700; color: #5BC0DE; margin-top: 20px;'>📊 Competition Limits:</p>
            <ul>
                <li>Maximum: <strong>{MAX_UPLOADS} uploads</strong></li>
                <li>Score Views: <strong>Unlimited ♾️</strong></li>
                <li>Current: <strong>{upload_count}/{MAX_UPLOADS}</strong></li>
            </ul>
            
            <p style='font-size: 1.1rem; font-weight: 700; color: #5BC0DE; margin-top: 25px;'>🎯 Score Guide:</p>
            <ul>
                <li><strong>80-100%</strong>: Excellent fit 🌟</li>
                <li><strong>60-79%</strong>: Good match ✨</li>
                <li><strong>Below 60%</strong>: Skills gap 💪</li>
            </ul>
            
            <p style='font-size: 1.1rem; font-weight: 700; color: #5BC0DE; margin-top: 25px;'>💡 Pro Tips:</p>
            <ul>
                <li>Submit different resume versions</li>
                <li>Check scores anytime</li>
                <li>Best score counts for ranking</li>
                <li>Privacy protected data 🔒</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # PAGE 2: My Scores
    elif page == "📈 My Scores":
        show_logo_header("My Score History")
        
        my_scores = get_participant_scores(st.session_state.participant_id)
        
        if not my_scores.empty:
            st.markdown('')
            st.markdown('<div class="card-header">📊 Your Submissions</div>', unsafe_allow_html=True)
            
            best_score = my_scores['score'].max()
            avg_score = my_scores['score'].mean()
            
            st.markdown(f"""
                <div class="score-display">
                    <div style="font-size: 1.5rem; opacity: 0.9; position: relative; z-index: 1; font-weight: 600;">Your Best Score</div>
                    <div class="score-number">{best_score:.1f}%</div>
                    <div style="font-size: 1.3rem; opacity: 0.9; position: relative; z-index: 1; font-weight: 600;">Out of {len(my_scores)} submission(s)</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Quick Stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Best Score</div>
                        <div class="metric-value">{best_score:.1f}%</div>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Average</div>
                        <div class="metric-value">{avg_score:.1f}%</div>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Total Submissions</div>
                        <div class="metric-value">{len(my_scores)}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📋 All Submissions")
            
            for idx, row in my_scores.iterrows():
                score_emoji = "🌟" if row['score'] >= 80 else "✨" if row['score'] >= 60 else "💪"
                st.markdown(f"""
                    <div class="leaderboard-item">
                        <div style="font-size: 2rem; margin-right: 20px;">{score_emoji}</div>
                        <div style="flex: 1;">
                            <div style="font-weight: 700; color: #0f2027; font-size: 1.2rem;">
                                Submission #{idx + 1}
                            </div>
                            <div style="color: #5BC0DE; margin-top: 10px; font-size: 1rem; font-weight: 600;">
                                Skills: {row['skills_count']} | Experience: {row['experience_years']} yrs | 
                                Date: {pd.to_datetime(row['submitted_at']).strftime('%d-%m-%Y %H:%M')}
                            </div>
                        </div>
                        <div style="font-size: 2.5rem; font-weight: 900; background: linear-gradient(135deg, #0f2027 0%, #2c5364 100%);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                            {row['score']:.1f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
                
                    <h3 style='color: white; text-align: center; font-size: 2rem;'>📭 No Submissions Yet</h3>
                    <p style='text-align: center; opacity: 0.9; font-size: 1.2rem; margin-top: 20px;'>Upload your resume to see scores here</p>
                </div>
            """, unsafe_allow_html=True)
    
    # PAGE 3: Leaderboard
    elif page == "🏆 Leaderboard":
        show_logo_header("Competition Leaderboard")
        
        leaderboard = get_leaderboard()
        
        if not leaderboard.empty:
            st.markdown('')
            st.markdown('<div class="card-header">🏆 Top 10 Performers</div>', unsafe_allow_html=True)
            
            # Top 3
            st.markdown("### 🎖️ Top 3 Winners")
            cols = st.columns(3)
            
            medals = ["🥇 Champion", "🥈 Runner-up", "🥉 Third Place"]
            colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
            
            for idx, (_, row) in enumerate(leaderboard.head(3).iterrows()):
                with cols[idx]:
                    st.markdown(f"""
                        <div style="text-align: center; padding: 40px 28px; 
                        background: linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(240,240,245,0.98) 100%);
                        border-radius: 24px; border: 5px solid {colors[idx]}; 
                        box-shadow: 0 12px 35px rgba(0,0,0,0.18);
                        transition: transform 0.3s ease;">
                            <div style="font-size: 3rem; margin-bottom: 12px;">{medals[idx].split()[0]}</div>
                            <div style="font-size: 1.4rem; color: {colors[idx]}; font-weight: 800; margin: 15px 0;">
                                {medals[idx].split()[1]}
                            </div>
                            <div style="font-size: 2.8rem; font-weight: 900; background: linear-gradient(135deg, #0f2027 0%, #2c5364 100%);
                            -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 18px 0;">
                                {row['score']:.1f}%
                            </div>
                            <div style="color: #5BC0DE; font-size: 1rem; font-weight: 700;">
                                {row['skills_count']} Skills | {row['experience']} Yrs
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("### 📊 Complete Rankings")
            
            for _, row in leaderboard.iterrows():
                badge = ""
                if row['rank'] <= 3:
                    badge = f"<span class='top-badge'>TOP {row['rank']}</span>"
                
                st.markdown(f"""
                    <div class="leaderboard-item">
                        <span class="leaderboard-rank">#{row['rank']}</span>
                        <div style="flex: 1;">
                            <div style="font-weight: 700; color: #0f2027; font-size: 1.2rem;">
                                Participant: {row['participant_id'][:14]}... {badge}
                            </div>
                            <div style="color: #5BC0DE; margin-top: 10px; font-size: 1rem; font-weight: 600;">
                                Skills: {row['skills_count']} | Experience: {row['experience']} years
                            </div>
                        </div>
                        <div style="font-size: 2.2rem; font-weight: 900; background: linear-gradient(135deg, #0f2027 0%, #2c5364 100%);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                            {row['score']:.1f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
                
                    <h3 style='color: white; text-align: center; font-size: 2rem;'>🎯 Be the First!</h3>
                    <p style='text-align: center; opacity: 0.9; font-size: 1.2rem; margin-top: 20px;'>No submissions yet. Start competing now!</p>
                </div>
            """, unsafe_allow_html=True)
    
    # PAGE 4: Stats
    elif page == "📊 Competition Stats":
        show_logo_header("Competition Statistics")
        
        stats = get_competition_stats()
        
        if stats and stats['total_participants'] > 0:
            st.markdown('')
            st.markdown('<div class="card-header">📊 Competition Overview</div>', unsafe_allow_html=True)
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            metrics_data = [
                ("Total Participants", stats["total_participants"], "👥"),
                ("Average Score", f"{stats['avg_score']:.1f}%", "📊"),
                ("Highest Score", f"{stats['top_score']:.1f}%", "🏆"),
                ("High Scorers (80+)", stats["high_scorers"], "⭐")
            ]
            
            for col, (label, value, icon) in zip([col1, col2, col3, col4], metrics_data):
                with col:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 2.8rem; margin-bottom: 12px;">{icon}</div>
                            <div class="metric-label">{label}</div>
                            <div class="metric-value">{value}</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📈 Score Distribution")
                
                df_dist = pd.DataFrame(stats['score_distribution'])
                fig_bar = px.bar(
                    df_dist,
                    x='range',
                    y='count',
                    labels={'range': 'Score Range', 'count': 'Participants'},
                    color='count',
                    color_continuous_scale=['#f44336', '#ffc107', '#4caf50']
                )
                fig_bar.update_layout(
                    showlegend=False,
                    height=380,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font={'color': '#0f2027', 'family': 'Inter', 'size': 13, 'weight': 600}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                st.markdown("### 🎓 Experience Levels")
                
                df_exp = pd.DataFrame(stats['experience_distribution'])
                fig_pie = px.pie(
                    df_exp,
                    values='count',
                    names='range',
                    color_discrete_sequence=['#0f2027', '#2c5364', '#5BC0DE', '#E6E4E6'],
                    hole=0.4
                )
                fig_pie.update_layout(
                    height=380,
                    paper_bgcolor='rgba(0,0,0,0)',
                    font={'color': '#0f2027', 'family': 'Inter', 'size': 13, 'weight': 600}
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
                
                    <h3 style='color: white; text-align: center; font-size: 2rem;'>📊 Coming Soon</h3>
                    <p style='text-align: center; opacity: 0.9; font-size: 1.2rem; margin-top: 20px;'>Statistics will appear once participants start submitting</p>
                </div>
            """, unsafe_allow_html=True)