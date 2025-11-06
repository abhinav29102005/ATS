import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from PIL import Image
import pymupdf
import spacy
import re
import uuid
from supabase import create_client, Client
# Supabase Configuration
SUPABASE_URL = "https://xsgjinwzxzkpjwwenjzj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhzZ2ppbnd6eHprcGp3d2VuanpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0NTIzMDcsImV4cCI6MjA3ODAyODMwN30.KnEN3YQuKk_tO7W47Kf_vmebu7QbtHOuxX2KMDhsn_k"
# Page config
st.set_page_config(
    page_title="MLSC Perfect CV Match 2025",
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

# Enhanced CSS with Professional Color Scheme (#2c5282, #4299e1)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main Background - Dark Blue Gradient */
    .main {
        background: linear-gradient(180deg, #1e3a5f 0%, #2c5282 100%);
        padding: 0 !important;
    }
    
    .stApp {
        background: transparent;
    }
    
    .block-container {
        padding: 1rem 3rem 2rem 3rem;
        max-width: 100%;
    }
    
    /* Sidebar Styling - Dark Blue */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a365d 0%, #2c5282 100%);
        padding-top: 2rem;
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Profile Card in Sidebar */
    .profile-card {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.15);
    }
    
    /* Upload Badge - Light Blue (#4299e1) */
    .upload-badge {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 25px;
        text-align: center;
        font-weight: 700;
        font-size: 1.1rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(66, 153, 225, 0.4);
    }
    
    /* Page Header */
    .page-header {
        background: white;
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    
    .page-title {
        font-size: 2rem;
        font-weight: 700;
        color: #2c5282;
        margin: 0;
    }
    
    /* Main Content Card */
    .content-card {
        background: white;
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
    }
    
    .card-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2c5282;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 3px solid #4299e1;
    }
    
    /* Info Banner */
    .info-banner {
        background: linear-gradient(135deg, #fef5e7 0%, #fdeaa3 100%);
        border-left: 5px solid #f59e0b;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1.5rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .info-banner-text {
        color: #92400e;
        font-weight: 600;
        font-size: 1.05rem;
    }
    
    /* Text Area Styling */
    .stTextArea textarea {
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #4299e1;
        box-shadow: 0 0 0 4px rgba(66, 153, 225, 0.1);
    }
    
    .stTextArea label {
        font-weight: 600;
        color: #2c5282;
        font-size: 1.05rem;
        margin-bottom: 0.5rem;
    }
    
    /* Input Fields */
    .stTextInput input {
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus {
        border-color: #4299e1;
        box-shadow: 0 0 0 4px rgba(66, 153, 225, 0.1);
    }
    
    .stTextInput label {
        font-weight: 600;
        color: #2c5282;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Buttons - Light Blue (#4299e1) */
    .stButton button {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        border: none;
        padding: 0.9rem 2.5rem;
        border-radius: 10px;
        font-weight: 700;
        font-size: 1.05rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(66, 153, 225, 0.3);
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(66, 153, 225, 0.4);
        background: linear-gradient(135deg, #3182ce 0%, #2c5282 100%);
    }
    
    .stButton button:disabled {
        background: #cbd5e0;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #4299e1 0%, #3182ce 100%);
        border-radius: 10px;
    }
    
    /* Leaderboard Items */
    .leaderboard-item {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border-left: 5px solid #4299e1;
        display: flex;
        align-items: center;
        gap: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .leaderboard-item:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .rank-badge {
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #2c5282 0%, #4299e1 100%);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.3rem;
        box-shadow: 0 4px 12px rgba(44, 82, 130, 0.3);
    }
    
    /* Registration Form */
    .register-container {
        background: white;
        padding: 3rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        max-width: 500px;
        margin: 3rem auto;
    }
    
    .register-title {
        font-size: 2rem;
        font-weight: 800;
        color: #2c5282;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .register-subtitle {
        text-align: center;
        color: #64748b;
        margin-bottom: 2rem;
        font-size: 1.05rem;
    }
    
    /* Score Display */
    .score-container {
        background: linear-gradient(135deg, #2c5282 0%, #4299e1 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 40px rgba(44, 82, 130, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .score-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.05); opacity: 0.8; }
    }
    
    .score-value {
        font-size: 5rem;
        font-weight: 800;
        color: white;
        margin: 0;
        text-shadow: 0 4px 20px rgba(0,0,0,0.2);
        position: relative;
        z-index: 1;
    }
    
    .score-label {
        font-size: 1.5rem;
        color: rgba(255,255,255,0.95);
        margin-top: 1rem;
        font-weight: 600;
        position: relative;
        z-index: 1;
    }
    
    /* Metric Boxes */
    .metric-box {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #4299e1;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #2c5282;
    }
    
    /* Skills Tags */
    .skill-tag {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        padding: 0.6rem 1.2rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.95rem;
        box-shadow: 0 2px 8px rgba(66, 153, 225, 0.3);
        transition: all 0.2s ease;
        display: inline-block;
        margin: 0.4rem;
    }
    
    .skill-tag:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4);
    }
    
    /* Guidelines Card */
    .guidelines-card {
        background: linear-gradient(135deg, #2c5282 0%, #1e3a5f 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(44, 82, 130, 0.3);
    }
    
    .guidelines-title {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid rgba(255,255,255,0.2);
    }
    
    .guidelines-section {
        margin-bottom: 1.5rem;
    }
    
    .guidelines-section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #4299e1;
        margin-bottom: 0.8rem;
    }
    
    .guidelines-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .guidelines-list li {
        padding: 0.5rem 0;
        padding-left: 1.5rem;
        position: relative;
        line-height: 1.6;
    }
    
    .guidelines-list li:before {
        content: "✓";
        position: absolute;
        left: 0;
        color: #4ade80;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== BACKEND FUNCTIONS ====================

@st.cache_resource
def load_nlp():
    """Load spaCy model with caching"""
    try:
        return spacy.load("en_core_web_sm")
    except:
        st.error("spaCy model not found. Install: python -m spacy download en_core_web_sm")
        return None

nlp = load_nlp()

@st.cache_resource
def get_supabase_client():
    """Initialize Supabase client"""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError:
        st.error("""
        ❌ Missing Supabase credentials!
        
        Create `.streamlit/secrets.toml` with:
        ```
        SUPABASE_URL = "https://xsgjinwzxzkpjwwenjzj.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhzZ2ppbnd6eHprcGp3d2VuanpqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0NTIzMDcsImV4cCI6MjA3ODAyODMwN30.KnEN3YQuKk_tO7W47Kf_vmebu7QbtHOuxX2KMDhsn_k"
        ```
        """)
        return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

supabase: Client = get_supabase_client()

def extract_pdf_text(uploaded_file):
    """Extract text from PDF"""
    try:
        pdf_bytes = uploaded_file.read()
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        text = "".join([page.get_text() + "\n" for page in doc])
        doc.close()
        return text
    except Exception as e:
        raise Exception(f"PDF extraction error: {str(e)}")

def parse_resume(text):
    """Parse resume and extract skills"""
    if not nlp:
        raise Exception("NLP model not loaded")
    
    skills_list = ['Python', 'Java', 'JavaScript', 'SQL', 'AWS', 'Docker', 'Kubernetes',
                   'React', 'Node.js', 'Django', 'Flask', 'PostgreSQL', 'MongoDB',
                   'Machine Learning', 'Data Science', 'Git', 'CI/CD', 'Agile', 'Scrum',
                   'TensorFlow', 'PyTorch', 'Pandas', 'NumPy']
    
    skills = list(dict.fromkeys([s for s in skills_list if s.lower() in text.lower()]))
    experience_years = max([int(m) for m in re.findall(r'(\d+)\+?\s*years?', text.lower())] or [0])
    
    return {'skills': skills, 'experience_years': experience_years}

def calculate_ats_score(resume_text, job_description):
    """Calculate ATS score"""
    parsed = parse_resume(resume_text)
    score = 0
    
    jd_lower = job_description.lower()
    matched_skills = [s for s in parsed['skills'] if s.lower() in jd_lower]
    if parsed['skills']:
        score += (len(matched_skills) / max(len(parsed['skills']), 1)) * 40
    
    exp_match = re.search(r'(\d+)\+?\s*years?', job_description.lower())
    required_exp = int(exp_match.group(1)) if exp_match else 2
    if parsed['experience_years'] >= required_exp:
        score += 30
    elif parsed['experience_years'] > 0:
        score += (parsed['experience_years'] / required_exp) * 30
    
    if nlp:
        jd_doc = nlp(job_description.lower())
        keywords = [t.text for t in jd_doc if not t.is_stop and t.is_alpha and len(t.text) > 3]
        keyword_matches = sum(1 for kw in keywords if kw in resume_text.lower())
        if keywords:
            score += min((keyword_matches / len(keywords)) * 30, 30)
    
    return {**parsed, 'score': round(min(score, 100), 2)}

def check_participant_exists(email):
    """Check if participant exists"""
    try:
        if not supabase:
            return None
        response = supabase.table('participants').select('*').eq('email', email).execute()
        return response.data[0] if response.data else None
    except:
        return None

def register_participant(name, email, mobile):
    """Register new participant"""
    try:
        if not supabase:
            return str(uuid.uuid4())
        
        data = {
            'id': str(uuid.uuid4()),
            'name': name,
            'email': email,
            'mobile': mobile,
            'upload_count': 0,
            'registered_at': datetime.now().isoformat()
        }
        
        response = supabase.table('participants').insert(data).execute()
        return data['id']
    except:
        return str(uuid.uuid4())

def save_participant_application(score, skills, experience, participant_id):
    """Save application"""
    try:
        if not supabase:
            return
        
        data = {
            'score': float(score),
            'skills': skills,
            'skills_count': len(skills),
            'experience_years': float(experience),
            'participant_id': participant_id,
            'submitted_at': datetime.now().isoformat()
        }
        
        supabase.table('applications').insert(data).execute()
        
        response = supabase.table('participants').select('upload_count').eq('id', participant_id).execute()
        if response.data:
            current_count = response.data[0]['upload_count']
            supabase.table('participants').update({'upload_count': current_count + 1}).eq('id', participant_id).execute()
        
    except Exception as e:
        raise Exception(f"Submission error: {str(e)}")

def get_participant_upload_count(participant_id):
    """Get upload count"""
    try:
        if not supabase:
            return 0
        response = supabase.table('participants').select('upload_count').eq('id', participant_id).execute()
        return response.data[0]['upload_count'] if response.data else 0
    except:
        return 0

def get_participant_scores(participant_id):
    """Get all scores"""
    try:
        if not supabase:
            return pd.DataFrame()
        response = supabase.table('applications').select('*').eq('participant_id', participant_id).order('submitted_at', desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def get_leaderboard():
    """Get top 10"""
    try:
        if not supabase:
            return pd.DataFrame()
        response = supabase.table('applications').select('*').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df = df.loc[df.groupby('participant_id')['score'].idxmax()]
            df = df.sort_values('score', ascending=False).head(10)
            df['rank'] = range(1, len(df) + 1)
            df = df.rename(columns={'experience_years': 'experience'})
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_competition_stats():
    """Get stats"""
    try:
        if not supabase:
            return None
        
        participants_response = supabase.table('participants').select('id').execute()
        total_participants = len(participants_response.data) if participants_response.data else 0
        
        response = supabase.table('applications').select('*').execute()
        
        if not response.data:
            return None
        
        df = pd.DataFrame(response.data)
        df_best = df.loc[df.groupby('participant_id')['score'].idxmax()]
        
        bins = [0, 60, 80, 100]
        labels = ['0-59%', '60-79%', '80-100%']
        df_best['score_range'] = pd.cut(df_best['score'], bins=bins, labels=labels, include_lowest=True)
        score_dist = df_best['score_range'].value_counts().reset_index()
        score_dist.columns = ['range', 'count']
        
        exp_bins = [0, 2, 5, 10, 50]
        exp_labels = ['0-2 yrs', '2-5 yrs', '5-10 yrs', '10+ yrs']
        df_best['exp_range'] = pd.cut(df_best['experience_years'], bins=exp_bins, labels=exp_labels, include_lowest=True)
        exp_dist = df_best['exp_range'].value_counts().reset_index()
        exp_dist.columns = ['range', 'count']
        
        return {
            'total_participants': total_participants,
            'avg_score': df_best['score'].mean(),
            'top_score': df_best['score'].max(),
            'high_scorers': len(df_best[df_best['score'] >= 80]),
            'score_distribution': score_dist.to_dict('records'),
            'experience_distribution': exp_dist.to_dict('records')
        }
    except:
        return None

def show_page_header(title):
    """Display page header with logo"""
    try:
        logo = Image.open("mlsc.png")
        col1, col2 = st.columns([1, 15])
        with col1:
            st.image(logo, width=60)
        with col2:
            st.markdown(f"<h1 class='page-title'>{title}</h1>", unsafe_allow_html=True)
    except:
        st.markdown(f"<h1 class='page-title'>{title}</h1>", unsafe_allow_html=True)

# ==================== UI PAGES ====================

# REGISTRATION PAGE
if not st.session_state.registered:
    # Centered logo
    try:
        logo = Image.open("mlsc.png")
        _, center_col, _ = st.columns([1, 1, 1])
        with center_col:
            st.image(logo, width=180)
    except:
        pass
    
    # Title
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style='color: white; font-size: 2.8rem; margin: 0; font-weight: 800;'>PERFECT CV MATCH 2025</h1>
            <p style='color: rgba(255,255,255,0.9); font-size: 1.2rem; margin: 1rem 0 0 0;'>Microsoft Learn Student Chapter @ TIET</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="register-container">', unsafe_allow_html=True)
        
        st.markdown('<div class="register-title">Participant Registration</div>', unsafe_allow_html=True)
        st.markdown('<div class="register-subtitle">Join the competition and showcase your skills</div>', unsafe_allow_html=True)
        
        with st.form("registration_form"):
            name = st.text_input("Full Name", placeholder="Enter your complete name")
            email = st.text_input("Email Address", placeholder="student@thapar.edu")
            mobile = st.text_input("Mobile Number", placeholder="+91 XXXXX XXXXX")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Register & Start Competing")
            
            if submit:
                errors = []
                if not name or len(name) < 3:
                    errors.append("Name must be at least 3 characters")
                if not email or '@' not in email or '@thapar.edu' not in email.lower():
                    errors.append("Valid Thapar email required")
                if not mobile or len(mobile.replace('+', '').replace(' ', '').replace('-', '')) < 10:
                    errors.append("Valid mobile number required")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    with st.spinner("Registering..."):
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
                        st.session_state.participant_data = {'name': name, 'email': email, 'mobile': mobile}
                        time.sleep(1)
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# MAIN APP
else:
    upload_count = get_participant_upload_count(st.session_state.participant_id)
    MAX_UPLOADS = 5
    
    # Sidebar
    with st.sidebar:
        try:
            logo = Image.open("mlsc.png")
            _, col, _ = st.columns([1, 1, 1])
            with col:
                st.image(logo, width=120)
        except:
            pass
        
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown(f"<div style='font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;'>{st.session_state.participant_data['name']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 0.9rem; opacity: 0.8;'>{st.session_state.participant_data['email']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 0.85rem; opacity: 0.7; margin-top: 0.5rem;'>ID: {st.session_state.participant_id[:8]}...</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown(f"<div class='upload-badge'>{upload_count}/5 Uploads</div>", unsafe_allow_html=True)
        
        upload_remaining = MAX_UPLOADS - upload_count
        if upload_remaining > 0:
            st.success(f"✓ {upload_remaining} remaining")
        else:
            st.error("✗ Limit reached")
        
        st.markdown("---")
        page = st.radio("Navigation", ["Submit Application", "My Scores", "Leaderboard", "Competition Stats"], label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("Exit"):
            st.session_state.registered = False
            st.rerun()
    
    # PAGE 1: Submit
    if page == "Submit Application":
        show_page_header("Submit Your Resume")
        
        if upload_count >= MAX_UPLOADS:
            st.error("Upload limit reached.")
            st.stop()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Resume Submission</div>', unsafe_allow_html=True)
            
            uploads_left = MAX_UPLOADS - upload_count
            st.markdown(f"""
                <div class="info-banner">
                    <div style="font-size: 1.5rem;">⚠</div>
                    <div class="info-banner-text">Only {uploads_left} upload(s) remaining!</div>
                </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader("Upload Your Resume (PDF)", type=['pdf'])
            job_description = st.text_area("Target Job Description", height=250, placeholder="Paste the job description...")
            
            if st.button("Submit & Calculate Score", disabled=(upload_count >= MAX_UPLOADS)):
                if uploaded_file and job_description:
                    try:
                        progress = st.progress(0)
                        status = st.empty()
                        
                        status.text("Reading resume...")
                        progress.progress(25)
                        time.sleep(0.4)
                        text = extract_pdf_text(uploaded_file)
                        
                        status.text("Analyzing...")
                        progress.progress(60)
                        time.sleep(0.6)
                        result = calculate_ats_score(text, job_description)
                        
                        status.text("Saving...")
                        progress.progress(90)
                        save_participant_application(result['score'], result['skills'], result['experience_years'], st.session_state.participant_id)
                        
                        progress.progress(100)
                        time.sleep(0.3)
                        progress.empty()
                        status.empty()
                        
                        st.success(f"Submission {upload_count + 1}/{MAX_UPLOADS} successful!")
                        
                        score = result['score']
                        verdict = "Excellent Match" if score >= 80 else "Good Match" if score >= 60 else "Needs Improvement"
                        
                        st.markdown(f"""
                            <div class="score-container">
                                <div class="score-value">{score:.1f}%</div>
                                <div class="score-label">{verdict}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=score,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={'text': "Match Score", 'font': {'size': 22, 'color': '#2c5282'}},
                            gauge={
                                'axis': {'range': [None, 100]},
                                'bar': {'color': "#4299e1"},
                                'steps': [
                                    {'range': [0, 60], 'color': "#fee2e2"},
                                    {'range': [60, 80], 'color': "#fef3c7"},
                                    {'range': [80, 100], 'color': "#d1fae5"}
                                ]
                            }
                        ))
                        fig.update_layout(height=350, margin=dict(l=20, r=20, t=60, b=20), paper_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(f"""
                                <div class="metric-box">
                                    <div class="metric-label">Skills Detected</div>
                                    <div class="metric-value">{len(result['skills'])}</div>
                                </div>
                            """, unsafe_allow_html=True)
                        with col_b:
                            st.markdown(f"""
                                <div class="metric-box">
                                    <div class="metric-label">Experience</div>
                                    <div class="metric-value">{result['experience_years']} yrs</div>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        if result['skills']:
                            st.markdown("**Detected Skills:**")
                            skills_html = "".join([f'<span class="skill-tag">{skill}</span>' for skill in result['skills']])
                            st.markdown(f'<div>{skills_html}</div>', unsafe_allow_html=True)
                        
                        time.sleep(1.5)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please upload resume and enter job description")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="guidelines-card">', unsafe_allow_html=True)
            st.markdown('<div class="guidelines-title">Guidelines</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="guidelines-section">
                <div class="guidelines-section-title">Limits:</div>
                <ul class="guidelines-list">
                    <li>Max: 5 uploads</li>
                    <li>Current: {upload_count}/5</li>
                    <li>Views: Unlimited</li>
                </ul>
            </div>
            <div class="guidelines-section">
                <div class="guidelines-section-title">Score Guide:</div>
                <ul class="guidelines-list">
                    <li>80-100%: Excellent</li>
                    <li>60-79%: Good</li>
                    <li>Below 60%: Improve</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # PAGE 2: Scores
    elif page == "My Scores":
        show_page_header("My Score History")
        
        my_scores = get_participant_scores(st.session_state.participant_id)
        
        if not my_scores.empty:
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            
            best_score = my_scores['score'].max()
            st.markdown(f"""
                <div class="score-container">
                    <div style="font-size: 1.3rem; opacity: 0.9; color: white; position: relative; z-index: 1;">Your Best Score</div>
                    <div class="score-value">{best_score:.1f}%</div>
                    <div style="font-size: 1.2rem; opacity: 0.9; color: white; position: relative; z-index: 1;">Out of {len(my_scores)} submission(s)</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="card-title">All Submissions</div>', unsafe_allow_html=True)
            
            for idx, row in my_scores.iterrows():
                st.markdown(f"""
                    <div class="leaderboard-item">
                        <div style="flex: 1;">
                            <div style="font-weight: 700; color: #2c5282; font-size: 1.1rem;">Submission #{idx + 1}</div>
                            <div style="color: #64748b; margin-top: 0.5rem; font-size: 0.9rem;">
                                Skills: {row['skills_count']} | Experience: {row['experience_years']} yrs
                            </div>
                        </div>
                        <div style="font-size: 2rem; font-weight: 800; color: #2c5282;">{row['score']:.1f}%</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No submissions yet.")
    
    # PAGE 3: Leaderboard
    elif page == "Leaderboard":
        show_page_header("Competition Leaderboard")
        
        leaderboard = get_leaderboard()
        
        if not leaderboard.empty:
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Top 10 Performers</div>', unsafe_allow_html=True)
            
            for _, row in leaderboard.iterrows():
                badge_color = "#FFD700" if row['rank'] == 1 else "#C0C0C0" if row['rank'] == 2 else "#CD7F32" if row['rank'] == 3 else "#4299e1"
                st.markdown(f"""
                    <div class="leaderboard-item">
                        <div class="rank-badge" style="background: {badge_color};">#{row['rank']}</div>
                        <div style="flex: 1;">
                            <div style="font-weight: 700; color: #2c5282;">ID: {row['participant_id'][:12]}...</div>
                            <div style="color: #64748b; margin-top: 0.3rem; font-size: 0.9rem;">
                                Skills: {row['skills_count']} | Exp: {row['experience']} yrs
                            </div>
                        </div>
                        <div style="font-size: 2rem; font-weight: 800; color: #2c5282;">{row['score']:.1f}%</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No submissions yet.")
    
    # PAGE 4: Stats
    elif page == "Competition Stats":
        show_page_header("Competition Statistics")
        
        stats = get_competition_stats()
        
        if stats and stats['total_participants'] > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            for col, label, value in zip([col1, col2, col3, col4], 
                                         ["Total Participants", "Avg Score", "Top Score", "High Scorers"],
                                         [stats["total_participants"], f"{stats['avg_score']:.1f}%", f"{stats['top_score']:.1f}%", stats["high_scorers"]]):
                with col:
                    st.markdown(f"""
                        <div class="metric-box">
                            <div class="metric-label">{label}</div>
                            <div class="metric-value">{value}</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                st.markdown('<div class="card-title">Score Distribution</div>', unsafe_allow_html=True)
                df = pd.DataFrame(stats['score_distribution'])
                fig = px.bar(df, x='range', y='count', color_discrete_sequence=['#4299e1'])
                fig.update_layout(height=350, showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                st.markdown('<div class="card-title">Experience Levels</div>', unsafe_allow_html=True)
                df = pd.DataFrame(stats['experience_distribution'])
                fig = px.pie(df, values='count', names='range', color_discrete_sequence=['#2c5282', '#dbeafe'])
                fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Statistics will appear soon.")
