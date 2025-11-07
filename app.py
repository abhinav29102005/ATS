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

# Custom CSS - Beautiful Modern Design with Color Scheme
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Main Background */
    .main {
        background: linear-gradient(135deg, #19395D 0%, #1E5796 100%);
        background-attachment: fixed;
    }
    
    .stApp {
        background: transparent;
    }
    
    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
    
    /* Logo Header */
    .logo-header {
        display: flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.98);
        padding: 20px 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    .logo-img {
        width: 55px;
        height: 55px;
        margin-right: 18px;
    }
    
    .logo-title {
        background: linear-gradient(135deg, #19395D 0%, #1E5796 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
    }
    
    /* Glass Morphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        padding: 40px;
        border-radius: 25px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.5);
        margin-bottom: 25px;
    }
    
    .logo-fixed {
        position: fixed;
        top: 20px;
        left: 20px;
        z-index: 1000;
        background: rgba(255, 255, 255, 0.95);
        padding: 10px;
        border-radius: 50%;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
    }

    .glass-card-dark {
        background: linear-gradient(135deg, rgba(25, 57, 93, 0.95) 0%, rgba(30, 87, 150, 0.95) 100%);
        backdrop-filter: blur(20px);
        padding: 40px;
        border-radius: 25px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(91, 192, 222, 0.3);
        color: white;
        margin-bottom: 25px;
    }
    
    /* Registration Container */
    .register-container {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(20px);
        padding: 50px;
        border-radius: 30px;
        box-shadow: 0 15px 60px rgba(0, 0, 0, 0.25);
        border: 2px solid rgba(91, 192, 222, 0.3);
        max-width: 520px;
        margin: 60px auto;
    }
    
    .register-title {
        background: linear-gradient(135deg, #19395D 0%, #1E5796 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 12px;
        text-align: center;
    }
    
    .register-subtitle {
        color: #5BC0DE;
        text-align: center;
        margin-bottom: 40px;
        font-size: 1.05rem;
        font-weight: 500;
    }
    
    /* Card Headers */
    .card-header {
        background: linear-gradient(135deg, #19395D 0%, #1E5796 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 30px;
        padding-bottom: 20px;
        border-bottom: 3px solid #5BC0DE;
    }
    
    /* Score Display - Stunning Design */
    .score-display {
        text-align: center;
        padding: 60px 40px;
        background: linear-gradient(135deg, #19395D 0%, #1E5796 50%, #5BC0DE 100%);
        border-radius: 30px;
        color: white;
        margin: 30px 0;
        box-shadow: 0 15px 50px rgba(25, 57, 93, 0.4);
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
        background: radial-gradient(circle, rgba(91, 192, 222, 0.2) 0%, transparent 70%);
        animation: pulse 3s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    .score-number {
        font-size: 6rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
        position: relative;
        z-index: 1;
    }
    
    .score-label {
        font-size: 1.6rem;
        opacity: 0.95;
        margin-top: 20px;
        font-weight: 600;
        position: relative;
        z-index: 1;
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(230, 228, 230, 0.98) 100%);
        backdrop-filter: blur(10px);
        padding: 35px 25px;
        border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
        border-top: 5px solid #5BC0DE;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.2);
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #19395D 0%, #1E5796 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 15px 0;
    }
    
    .metric-label {
        color: #5BC0DE;
        font-size: 1.05rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 700;
    }
    
    /* Leaderboard Items */
    .leaderboard-rank {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #19395D 0%, #1E5796 100%);
        color: white;
        border-radius: 50%;
        font-weight: 800;
        font-size: 1.4rem;
        margin-right: 20px;
        box-shadow: 0 5px 20px rgba(25, 57, 93, 0.4);
    }
    
    .leaderboard-item {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(230, 228, 230, 0.95) 100%);
        backdrop-filter: blur(10px);
        padding: 25px;
        border-radius: 18px;
        margin: 18px 0;
        border-left: 6px solid #5BC0DE;
        display: flex;
        align-items: center;
        transition: all 0.3s ease;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.08);
    }
    
    .leaderboard-item:hover {
        transform: translateX(10px);
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.15);
        border-left-color: #19395D;
    }
    
    .top-badge {
        background: linear-gradient(135deg, #5BC0DE 0%, #1E5796 100%);
        color: white;
        padding: 10px 24px;
        border-radius: 25px;
        font-weight: 700;
        font-size: 0.95rem;
        box-shadow: 0 4px 15px rgba(91, 192, 222, 0.4);
    }
    
    /* Limit Badges */
    .limit-badge {
        display: inline-block;
        padding: 12px 24px;
        background: linear-gradient(135deg, rgba(91, 192, 222, 0.2) 0%, rgba(30, 87, 150, 0.2) 100%);
        border: 2px solid #5BC0DE;
        border-radius: 25px;
        color: #19395D;
        font-weight: 700;
        font-size: 1rem;
        margin: 12px 8px;
        box-shadow: 0 4px 15px rgba(91, 192, 222, 0.2);
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
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #5BC0DE 0%, #1E5796 100%);
        color: white;
        border: none;
        padding: 16px 40px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(91, 192, 222, 0.4);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton>button:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 35px rgba(91, 192, 222, 0.5);
        background: linear-gradient(135deg, #1E5796 0%, #19395D 100%);
    }
    
    .stButton>button:disabled {
        background: linear-gradient(135deg, #E6E4E6 0%, #cccccc 100%);
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(135deg, #5BC0DE 0%, #1E5796 100%);
    }
    
    /* Input Fields */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        border-radius: 12px;
        border: 2px solid #E6E4E6;
        padding: 14px;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #5BC0DE;
        box-shadow: 0 0 0 3px rgba(91, 192, 222, 0.2);
    }
    
    /* File Uploader */
    .stFileUploader {
        background: rgba(91, 192, 222, 0.1);
        border-radius: 15px;
        border: 2px dashed #5BC0DE;
        padding: 25px;
    }
    
    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #19395D 0%, #1E5796 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Sidebar Headers - Make them explicitly white */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6 {
        color: white !important;
        background: none !important;
        -webkit-text-fill-color: white !important;
    }
    
    /* Sidebar Markdown text */
    [data-testid="stSidebar"] .element-container p,
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        background: linear-gradient(135deg, #19395D 0%, #1E5796 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }
    
    /* Info Box */
    .info-box {
        background: linear-gradient(135deg, rgba(91, 192, 222, 0.15) 0%, rgba(30, 87, 150, 0.15) 100%);
        backdrop-filter: blur(10px);
        padding: 30px;
        border-radius: 18px;
        border-left: 6px solid #5BC0DE;
        margin: 25px 0;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.08);
    }
    
    /* Competition Banner */
    .competition-banner {
        background: linear-gradient(135deg, #19395D 0%, #1E5796 50%, #5BC0DE 100%);
        color: white;
        padding: 45px 35px;
        border-radius: 25px;
        text-align: center;
        margin-bottom: 40px;
        box-shadow: 0 15px 50px rgba(25, 57, 93, 0.3);
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
        background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
        animation: rotate 20s linear infinite;
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Skill Tags */
    .skill-tag {
        display: inline-block;
        padding: 10px 20px;
        background: linear-gradient(135deg, #5BC0DE 0%, #1E5796 100%);
        color: white;
        border-radius: 25px;
        margin: 8px;
        font-weight: 600;
        font-size: 0.95rem;
        box-shadow: 0 4px 15px rgba(91, 192, 222, 0.3);
        transition: all 0.3s ease;
    }
    
    .skill-tag:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(91, 192, 222, 0.4);
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.15) 0%, rgba(56, 142, 60, 0.15) 100%);
        border: 2px solid #4caf50;
        border-radius: 12px;
        color: #2e7d32;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.15) 0%, rgba(211, 47, 47, 0.15) 100%);
        border: 2px solid #f44336;
        border-radius: 12px;
        color: #c62828;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.15) 0%, rgba(255, 152, 0, 0.15) 100%);
        border: 2px solid #ffc107;
        border-radius: 12px;
        color: #ff6f00;
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(91, 192, 222, 0.15) 0%, rgba(30, 87, 150, 0.15) 100%);
        border: 2px solid #5BC0DE;
        border-radius: 12px;
        color: #1E5796;
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
            st.image(logo, width=55)
        with col2:
            st.markdown(f"<div class='logo-title'>{title}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except:
        st.markdown(f"<div class='logo-header'><div class='logo-title'>{title}</div></div>", unsafe_allow_html=True)

# REGISTRATION PAGE
if not st.session_state.registered:
    # Fixed logo in top-left corner
    try:
        logo = Image.open("mlsc.png")
        st.markdown('<div class="logo-fixed">', unsafe_allow_html=True)
        st.image(logo, width=60)
        st.markdown('</div>', unsafe_allow_html=True)
    except:
        pass
    
    st.markdown("""
        <div class="competition-banner">
            <h1 style='color: white; margin: 0; font-size: 2.8rem; position: relative; z-index: 1; text-shadow: 0 4px 20px rgba(0,0,0,0.3);'>PERFECT CV MATCH 2025</h1>
            <p style='margin: 15px 0 0 0; font-size: 1.2rem; opacity: 0.95; position: relative; z-index: 1;'>Microsoft Learn Student Chapter @ TIET</p>
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
                placeholder="student@thapar.edu only",
                help="Your institutional email address"
            )
            
            mobile = st.text_input(
                "Mobile Number",
                placeholder="+91 XXXXX XXXXX",
                help="10-digit mobile number"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Register & Start Competing", use_container_width=True)
            
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
                        st.error(error)
                else:
                    with st.spinner("Registering participant..."):
                        time.sleep(0.8)
                        
                        existing = check_participant_exists(email)
                        
                        if existing:
                            participant_id = existing['id']
                            st.info("Welcome back! You are already registered.")
                        else:
                            participant_id = register_participant(name, email, mobile)
                            st.success("Registration Successful!")
                        
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
            <h4 style='color: #1E5796; margin-top: 0; font-weight: 700;'>Competition Rules</h4>
            <ul style='color: #19395D; line-height: 2; font-weight: 500;'>
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
            st.image(logo, width=130)
        except:
            pass
        
        st.markdown("---")
        st.markdown("### Participant Profile")
        st.write(f"**{st.session_state.participant_data['name']}**")
        st.write(f"📧 {st.session_state.participant_data['email']}")
        st.write(f"🆔 {st.session_state.participant_id[:8]}...")
        
        st.markdown("---")
        st.markdown("### Upload Limit")
        
        upload_remaining = MAX_UPLOADS - upload_count
        if upload_remaining > 1:
            badge_class = "limit-badge"
        elif upload_remaining == 1:
            badge_class = "limit-badge limit-warning"
        else:
            badge_class = "limit-badge limit-danger"
        
        st.markdown(f"<div class='{badge_class}'>{upload_count}/{MAX_UPLOADS} Uploads</div>", unsafe_allow_html=True)
        
        if upload_remaining > 0:
            st.success(f"✓ {upload_remaining} remaining")
        else:
            st.error("✗ Limit reached")
        
        st.markdown("---")
        st.markdown("### Navigation")
        page = st.radio(
            "",
            ["Submit Application", "My Scores", "Leaderboard", "Competition Stats"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        if st.button("Exit Competition", use_container_width=True):
            st.session_state.registered = False
            st.session_state.participant_id = None
            st.session_state.participant_data = {}
            st.rerun()
    
    # PAGE 1: Submit Application
    if page == "Submit Application":
        show_logo_header("Submit Your Resume")
        
        if upload_count >= MAX_UPLOADS:
            st.markdown(f"""
                <div class="glass-card-dark">
                    <h2 style='color: white; text-align: center;'>Upload Limit Reached</h2>
                    <p style='text-align: center; font-size: 1.1rem; opacity: 0.9;'>
                        You have used all {MAX_UPLOADS} uploads. View your scores in 'My Scores' section.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            st.stop()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<div class="card-header">Resume Submission</div>', unsafe_allow_html=True)
            
            uploads_left = MAX_UPLOADS - upload_count
            if uploads_left <= 2:
                st.warning(f"⚠ Only {uploads_left} upload(s) remaining!")
            else:
                st.info(f"ℹ {uploads_left} of {MAX_UPLOADS} uploads remaining")
            
            uploaded_file = st.file_uploader(
                "Upload Your Resume (PDF)",
                type=['pdf'],
                help="Maximum file size: 20MB"
            )
            
            job_description = st.text_area(
                "Target Job Description",
                height=250,
                placeholder="Paste the job description you're targeting...\n\nExample:\nWe are looking for a Software Developer with 3+ years of experience...",
                help="Paste the complete job description"
            )
            
            if st.button("Submit & Calculate Score", type="primary", use_container_width=True, disabled=(upload_count >= MAX_UPLOADS)):
                if uploaded_file and job_description:
                    try:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("📄 Reading your resume...")
                        progress_bar.progress(20)
                        time.sleep(0.4)
                        text = extract_pdf_text(uploaded_file)
                        
                        status_text.text("🤖 Analyzing with AI engine...")
                        progress_bar.progress(50)
                        time.sleep(0.6)
                        result = calculate_ats_score(text, job_description)
                        
                        status_text.text("💾 Saving results...")
                        progress_bar.progress(80)
                        time.sleep(0.4)
                        
                        save_participant_application(
                            result['score'],
                            result['skills'],
                            result['experience_years'],
                            st.session_state.participant_id
                        )
                        
                        progress_bar.progress(100)
                        time.sleep(0.3)
                        progress_bar.empty()
                        status_text.empty()
                        
                        st.success(f"✅ Submission {upload_count + 1}/{MAX_UPLOADS} successful!")
                        
                        # Score Display
                        score = result['score']
                        if score >= 80:
                            verdict = "Excellent Match"
                        elif score >= 60:
                            verdict = "Good Match"
                        else:
                            verdict = "Needs Improvement"
                        
                        st.markdown(f"""
                            <div class="score-display">
                                <div class="score-number">{score:.1f}%</div>
                                <div class="score-label">{verdict}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Gauge Chart
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=score,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={'text': "Match Score", 'font': {'size': 24, 'color': '#19395D', 'family': 'Poppins'}},
                            gauge={
                                'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': '#19395D'},
                                'bar': {'color': "#5BC0DE", 'thickness': 0.8},
                                'steps': [
                                    {'range': [0, 60], 'color': "rgba(244, 67, 54, 0.2)"},
                                    {'range': [60, 80], 'color': "rgba(255, 193, 7, 0.2)"},
                                    {'range': [80, 100], 'color': "rgba(76, 175, 80, 0.2)"}
                                ],
                                'threshold': {
                                    'line': {'color': "#1E5796", 'width': 6},
                                    'thickness': 0.85,
                                    'value': 85
                                }
                            }
                        ))
                        fig.update_layout(
                            height=380,
                            margin=dict(l=20, r=20, t=70, b=20),
                            paper_bgcolor='rgba(0,0,0,0)',
                            font={'color': '#19395D', 'family': 'Poppins', 'size': 14}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Analysis
                        st.markdown("### Analysis Summary")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Skills Detected", f"{len(result['skills'])} skills", 
                                     delta="High" if len(result['skills']) >= 5 else "Low")
                        with col_b:
                            st.metric("Experience", f"{result['experience_years']} years",
                                     delta="Strong" if result['experience_years'] >= 3 else "Entry")
                        
                        if result['skills']:
                            st.markdown("### Detected Skills")
                            skills_html = "".join([
                                f'<span class="skill-tag">{skill}</span>'
                                for skill in result['skills']
                            ])
                            st.markdown(f'<div style="text-align: center;">{skills_html}</div>', unsafe_allow_html=True)
                        
                        time.sleep(1.5)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ Please upload resume and enter job description")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<h3 style="color: white; border-bottom: 3px solid #5BC0DE; padding-bottom: 15px;">Guidelines</h3>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='color: white; line-height: 1.8;'>
            <p style='font-size: 1.05rem; font-weight: 600; color: #5BC0DE;'>Competition Limits:</p>
            <ul>
                <li>Maximum: <strong>{MAX_UPLOADS} uploads</strong></li>
                <li>Score Views: <strong>Unlimited</strong></li>
                <li>Current: <strong>{upload_count}/{MAX_UPLOADS}</strong></li>
            </ul>
            
            <p style='font-size: 1.05rem; font-weight: 600; color: #5BC0DE; margin-top: 20px;'>Score Guide:</p>
            <ul>
                <li><strong>80-100%</strong>: Excellent fit</li>
                <li><strong>60-79%</strong>: Good match</li>
                <li><strong>Below 60%</strong>: Skills gap</li>
            </ul>
            
            <p style='font-size: 1.05rem; font-weight: 600; color: #5BC0DE; margin-top: 20px;'>Pro Tips:</p>
            <ul>
                <li>Submit different resume versions</li>
                <li>Check scores anytime</li>
                <li>Best score counts for ranking</li>
                <li>Privacy protected data</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # PAGE 2: My Scores
    elif page == "My Scores":
        show_logo_header("My Score History")
        
        my_scores = get_participant_scores(st.session_state.participant_id)
        
        if not my_scores.empty:
            st.markdown('<div class="card-header">Your Submissions</div>', unsafe_allow_html=True)
            
            best_score = my_scores['score'].max()
            st.markdown(f"""
                <div class="score-display">
                    <div style="font-size: 1.4rem; opacity: 0.9; position: relative; z-index: 1;">Your Best Score</div>
                    <div class="score-number">{best_score:.1f}%</div>
                    <div style="font-size: 1.2rem; opacity: 0.9; position: relative; z-index: 1;">Out of {len(my_scores)} submission(s)</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### All Submissions")
            
            for idx, row in my_scores.iterrows():
                st.markdown(f"""
                    <div class="leaderboard-item">
                        <div style="flex: 1;">
                            <div style="font-weight: 600; color: #19395D; font-size: 1.15rem;">
                                Submission #{idx + 1}
                            </div>
                            <div style="color: #5BC0DE; margin-top: 8px; font-size: 0.95rem;">
                                Skills: {row['skills_count']} | Experience: {row['experience_years']} yrs | 
                                Date: {pd.to_datetime(row['submitted_at']).strftime('%d-%m-%Y %H:%M')}
                            </div>
                        </div>
                        <div style="font-size: 2.2rem; font-weight: 800; color: #1E5796;">
                            {row['score']:.1f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="glass-card-dark">
                    <h3 style='color: white; text-align: center;'>No Submissions Yet</h3>
                    <p style='text-align: center; opacity: 0.9;'>Upload your resume to see scores here</p>
                </div>
            """, unsafe_allow_html=True)
    
    # PAGE 3: Leaderboard
    elif page == "Leaderboard":
        show_logo_header("Competition Leaderboard")
        
        leaderboard = get_leaderboard()
        
        if not leaderboard.empty:
            st.markdown('<div class="card-header">Top 10 Performers</div>', unsafe_allow_html=True)
            
            # Top 3
            st.markdown("### Top 3 Winners")
            cols = st.columns(3)
            
            medals = ["🥇 Champion", "🥈 Runner-up", "🥉 Third Place"]
            colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
            
            for idx, (_, row) in enumerate(leaderboard.head(3).iterrows()):
                with cols[idx]:
                    st.markdown(f"""
                        <div style="text-align: center; padding: 35px 25px; 
                        background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(230,228,230,0.95) 100%);
                        border-radius: 20px; border: 4px solid {colors[idx]}; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
                            <div style="font-size: 2.5rem; margin-bottom: 10px;">{medals[idx].split()[0]}</div>
                            <div style="font-size: 1.3rem; color: {colors[idx]}; font-weight: 700; margin: 12px 0;">
                                {medals[idx].split()[1]}
                            </div>
                            <div style="font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #19395D 0%, #1E5796 100%);
                            -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 15px 0;">
                                {row['score']:.1f}%
                            </div>
                            <div style="color: #5BC0DE; font-size: 0.95rem; font-weight: 600;">
                                {row['skills_count']} Skills | {row['experience']} Yrs
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Complete Rankings")
            
            for _, row in leaderboard.iterrows():
                badge = ""
                if row['rank'] <= 3:
                    badge = f"<span class='top-badge'>TOP {row['rank']}</span>"
                
                st.markdown(f"""
                    <div class="leaderboard-item">
                        <span class="leaderboard-rank">#{row['rank']}</span>
                        <div style="flex: 1;">
                            <div style="font-weight: 600; color: #19395D; font-size: 1.15rem;">
                                Participant: {row['participant_id'][:14]}... {badge}
                            </div>
                            <div style="color: #5BC0DE; margin-top: 8px; font-size: 0.95rem;">
                                Skills: {row['skills_count']} | Experience: {row['experience']} years
                            </div>
                        </div>
                        <div style="font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #19395D 0%, #1E5796 100%);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                            {row['score']:.1f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="glass-card-dark">
                    <h3 style='color: white; text-align: center;'>Be the First!</h3>
                    <p style='text-align: center; opacity: 0.9;'>No submissions yet. Start competing now!</p>
                </div>
            """, unsafe_allow_html=True)
    
    # PAGE 4: Stats
    elif page == "Competition Stats":
        show_logo_header("Competition Statistics")
        
        stats = get_competition_stats()
        
        if stats and stats['total_participants'] > 0:
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
                            <div style="font-size: 2.5rem; margin-bottom: 10px;">{icon}</div>
                            <div class="metric-label">{label}</div>
                            <div class="metric-value">{value}</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="card-header">Score Distribution</div>', unsafe_allow_html=True)
                
                df_dist = pd.DataFrame(stats['score_distribution'])
                fig_bar = px.bar(
                    df_dist,
                    x='range',
                    y='count',
                    labels={'range': 'Score Range', 'count': 'Participants'},
                    color_discrete_sequence=['#5BC0DE']
                )
                fig_bar.update_layout(
                    showlegend=False,
                    height=360,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font={'color': '#19395D', 'family': 'Poppins', 'size': 13}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="card-header">Experience Levels</div>', unsafe_allow_html=True)
                
                df_exp = pd.DataFrame(stats['experience_distribution'])
                fig_pie = px.pie(
                    df_exp,
                    values='count',
                    names='range',
                    color_discrete_sequence=['#19395D', '#1E5796', '#5BC0DE', '#E6E4E6']
                )
                fig_pie.update_layout(
                    height=360,
                    paper_bgcolor='rgba(0,0,0,0)',
                    font={'color': '#19395D', 'family': 'Poppins', 'size': 13}
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="glass-card-dark">
                    <h3 style='color: white; text-align: center;'>Coming Soon</h3>
                    <p style='text-align: center; opacity: 0.9;'>Statistics will appear once participants start submitting</p>
                </div>
            """, unsafe_allow_html=True)