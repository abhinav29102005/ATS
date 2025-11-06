import pymupdf
import spacy
import re
import streamlit as st
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
import uuid
import hashlib

@st.cache_resource
def load_nlp():
    """Load NLP model with caching"""
    try:
        return spacy.load("en_core_web_sm")
    except:
        st.warning("⚠️ NLP model not available. Using basic parsing.")
        return None

nlp = load_nlp()

@st.cache_resource
def get_supabase_client():
    """Initialize Supabase client with caching"""
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"❌ Database connection error: {str(e)}")
        return None

supabase: Client = get_supabase_client()

def extract_pdf_text(uploaded_file):
    """Extract text from PDF with error handling"""
    try:
        pdf_bytes = uploaded_file.read()
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        
        # Extract text from all pages
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        
        doc.close()
        text = "\n".join(text_parts)
        
        if not text.strip():
            raise Exception("PDF appears to be empty or contains only images")
        
        return text
    except Exception as e:
        raise Exception(f"PDF extraction error: {str(e)}")

def parse_resume(text):
    """Enhanced resume parsing with better skill detection"""
    if not text:
        raise Exception("No text content found in resume")
    
    # Expanded skill list with more technologies
    skills_list = [
        # Programming Languages
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust', 'PHP', 'Ruby', 'Swift', 'Kotlin',
        
        # Web Technologies
        'React', 'Angular', 'Vue.js', 'Node.js', 'Express', 'Django', 'Flask', 'FastAPI', 'Spring', 'ASP.NET',
        
        # Databases
        'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Cassandra', 'Oracle', 'DynamoDB',
        
        # Cloud & DevOps
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'GitLab', 'Terraform', 'Ansible',
        
        # Data Science & ML
        'Machine Learning', 'Deep Learning', 'Data Science', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn',
        
        # Other Tools
        'Git', 'Agile', 'Scrum', 'REST API', 'GraphQL', 'Microservices', 'Linux', 'HTML', 'CSS', 'SASS'
    ]
    
    # Case-insensitive skill matching with word boundaries
    text_lower = text.lower()
    skills = []
    
    for skill in skills_list:
        # Use regex for more accurate matching
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            skills.append(skill)
    
    # Remove duplicates while preserving order
    skills = list(dict.fromkeys(skills))
    
    # Enhanced experience extraction
    experience_years = 0
    
    # Multiple patterns for experience detection
    patterns = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'experience\s+(?:of\s+)?(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs?\s+(?:of\s+)?experience',
        r'(\d+)\+?\s*years?\s+(?:in|of)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            experience_years = max([int(m) for m in matches])
            break
    
    return {
        'skills': skills,
        'experience_years': experience_years
    }

def calculate_ats_score(resume_text, job_description):
    """Enhanced ATS score calculation with better matching"""
    if not resume_text or not job_description:
        raise Exception("Both resume and job description are required")
    
    parsed = parse_resume(resume_text)
    score = 0
    
    jd_lower = job_description.lower()
    resume_lower = resume_text.lower()
    
    # 1. Skills Matching (40 points)
    jd_skills = []
    for skill in parsed['skills']:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, jd_lower):
            jd_skills.append(skill)
    
    if parsed['skills']:
        skill_match_ratio = len(jd_skills) / max(len(parsed['skills']), 1)
        score += min(skill_match_ratio * 40, 40)
    
    # 2. Experience Matching (30 points)
    exp_match = re.search(r'(\d+)\+?\s*years?', job_description.lower())
    required_exp = int(exp_match.group(1)) if exp_match else 2
    
    if parsed['experience_years'] >= required_exp:
        score += 30
    elif parsed['experience_years'] > 0:
        score += (parsed['experience_years'] / required_exp) * 30
    
    # 3. Keyword Matching (30 points)
    if nlp:
        jd_doc = nlp(job_description.lower())
        # Extract meaningful keywords (nouns, verbs, adjectives)
        keywords = [
            t.text for t in jd_doc 
            if not t.is_stop and t.is_alpha and len(t.text) > 3 
            and t.pos_ in ['NOUN', 'VERB', 'ADJ', 'PROPN']
        ]
        
        # Count keyword matches
        keyword_matches = sum(1 for kw in keywords if kw in resume_lower)
        
        if keywords:
            keyword_score = min((keyword_matches / len(keywords)) * 30, 30)
            score += keyword_score
    else:
        # Fallback: Simple word matching
        jd_words = set(w.lower() for w in job_description.split() if len(w) > 3)
        resume_words = set(w.lower() for w in resume_text.split() if len(w) > 3)
        common_words = jd_words.intersection(resume_words)
        
        if jd_words:
            score += min((len(common_words) / len(jd_words)) * 30, 30)
    
    return {
        **parsed,
        'score': round(min(score, 100), 2),
        'matched_skills': jd_skills
    }

def check_participant_exists(email):
    """Check if participant already registered with error handling"""
    try:
        if not supabase:
            return None
        
        response = supabase.table('participants').select('*').eq('email', email.lower()).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error checking registration: {str(e)}")
        return None

def register_participant(name, email, mobile):
    """Register new participant with validation"""
    try:
        if not supabase:
            # Fallback: generate UUID without database
            return str(uuid.uuid4())
        
        # Check if already exists
        existing = check_participant_exists(email)
        if existing:
            return existing['id']
        
        participant_id = str(uuid.uuid4())
        
        data = {
            'id': participant_id,
            'name': name.strip(),
            'email': email.lower().strip(),
            'mobile': mobile.strip(),
            'upload_count': 0,
            'view_count': 0,
            'registered_at': datetime.now().isoformat()
        }
        
        response = supabase.table('participants').insert(data).execute()
        return participant_id
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return str(uuid.uuid4())

def save_participant_application(score, skills, experience, participant_id):
    """Save competition application with transaction safety"""
    try:
        if not supabase:
            st.warning("⚠️ Running in offline mode - data not saved")
            return
        
        # Save application
        data = {
            'score': float(score),
            'skills': skills,
            'skills_count': len(skills),
            'experience_years': float(experience),
            'participant_id': participant_id,
            'submitted_at': datetime.now().isoformat()
        }
        
        supabase.table('applications').insert(data).execute()
        
        # Increment upload count atomically
        response = supabase.table('participants')\
            .select('upload_count')\
            .eq('id', participant_id)\
            .execute()
        
        if response.data:
            current_count = response.data[0]['upload_count']
            supabase.table('participants')\
                .update({'upload_count': current_count + 1})\
                .eq('id', participant_id)\
                .execute()
        
    except Exception as e:
        raise Exception(f"Submission error: {str(e)}")

def get_participant_upload_count(participant_id):
    """Get number of uploads by participant with caching"""
    try:
        if not supabase:
            return 0
        
        response = supabase.table('participants')\
            .select('upload_count')\
            .eq('id', participant_id)\
            .execute()
        
        return response.data[0]['upload_count'] if response.data else 0
    except Exception as e:
        st.error(f"Error fetching upload count: {str(e)}")
        return 0

def get_participant_view_count(participant_id):
    """Get number of score views by participant"""
    try:
        if not supabase:
            return 0
        
        response = supabase.table('participants')\
            .select('view_count')\
            .eq('id', participant_id)\
            .execute()
        
        return response.data[0]['view_count'] if response.data else 0
    except Exception as e:
        return 0

def increment_view_count(participant_id):
    """Increment view count when participant checks scores"""
    try:
        if not supabase:
            return
        
        response = supabase.table('participants')\
            .select('view_count')\
            .eq('id', participant_id)\
            .execute()
        
        if response.data:
            current_count = response.data[0]['view_count']
            supabase.table('participants')\
                .update({'view_count': current_count + 1})\
                .eq('id', participant_id)\
                .execute()
    except:
        pass

def get_participant_scores(participant_id):
    """Get all scores for a specific participant with sorting"""
    try:
        if not supabase:
            return pd.DataFrame()
        
        response = supabase.table('applications')\
            .select('*')\
            .eq('participant_id', participant_id)\
            .order('score', desc=True)\
            .execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            # Ensure proper data types
            df['score'] = pd.to_numeric(df['score'])
            df['skills_count'] = pd.to_numeric(df['skills_count'])
            df['experience_years'] = pd.to_numeric(df['experience_years'])
            return df
        
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching scores: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def get_leaderboard():
    """Get top 10 UNIQUE participants by best score with optimized query"""
    try:
        if not supabase:
            return pd.DataFrame()
        
        # Try using RPC function first
        try:
            response = supabase.rpc('get_leaderboard').execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                df['rank'] = range(1, len(df) + 1)
                df = df.rename(columns={'experience_years': 'experience'})
                return df.head(10)
        except:
            pass
        
        # Fallback: Manual grouping
        response = supabase.table('applications').select('*').execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            # Get best score per participant
            df = df.loc[df.groupby('participant_id')['score'].idxmax()]
            df = df.sort_values('score', ascending=False).head(10)
            df['rank'] = range(1, len(df) + 1)
            df = df.rename(columns={'experience_years': 'experience'})
            
            # Ensure proper data types
            df['score'] = pd.to_numeric(df['score'])
            df['skills_count'] = pd.to_numeric(df['skills_count'])
            
            return df
        
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching leaderboard: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_competition_stats():
    """Get overall competition statistics with proper aggregation"""
    try:
        if not supabase:
            return None
        
        # Get unique participants count
        participants_response = supabase.table('participants').select('id').execute()
        total_participants = len(participants_response.data) if participants_response.data else 0
        
        # Get all applications
        response = supabase.table('applications').select('*').execute()
        
        if not response.data or total_participants == 0:
            return None
        
        df = pd.DataFrame(response.data)
        
        # Convert to proper numeric types
        df['score'] = pd.to_numeric(df['score'])
        df['experience_years'] = pd.to_numeric(df['experience_years'])
        
        # Get best score per participant for stats
        df_best = df.loc[df.groupby('participant_id')['score'].idxmax()]
        
        # Score distribution
        bins = [0, 60, 80, 100]
        labels = ['0-59%', '60-79%', '80-100%']
        df_best['score_range'] = pd.cut(df_best['score'], bins=bins, labels=labels, include_lowest=True)
        score_dist = df_best['score_range'].value_counts().sort_index().reset_index()
        score_dist.columns = ['range', 'count']
        
        # Experience distribution
        exp_bins = [0, 2, 5, 10, 50]
        exp_labels = ['0-2 yrs', '2-5 yrs', '5-10 yrs', '10+ yrs']
        df_best['exp_range'] = pd.cut(df_best['experience_years'], bins=exp_bins, labels=exp_labels, include_lowest=True)
        exp_dist = df_best['exp_range'].value_counts().sort_index().reset_index()
        exp_dist.columns = ['range', 'count']
        
        return {
            'total_participants': total_participants,
            'avg_score': round(df_best['score'].mean(), 2),
            'top_score': round(df_best['score'].max(), 2),
            'high_scorers': len(df_best[df_best['score'] >= 80]),
            'score_distribution': score_dist.to_dict('records'),
            'experience_distribution': exp_dist.to_dict('records')
        }
    except Exception as e:
        st.error(f"Error fetching stats: {str(e)}")
        return None