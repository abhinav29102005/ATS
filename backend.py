import pymupdf
import spacy
import re
import streamlit as st
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
import uuid
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
#spacy nlp
@st.cache_resource
def load_nlp():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        logger.error("Spacy model not found")
        st.error("⚠️ NLP model not available. Please install: python -m spacy download en_core_web_sm")
        return None
    except Exception as e:
        logger.error(f"Error loading spacy: {e}")
        st.error(f"⚠️ Error loading NLP model: {str(e)}")
        return None

nlp = load_nlp()
#supabase call
@st.cache_resource
def get_supabase_client():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError as e:
        logger.error(f"Supabase secret missing: {e}")
        st.error(f"⚠️ Supabase configuration missing: {e}")
        return None
    except Exception as e:
        logger.error(f"Supabase connection failed: {e}")
        st.error(f"⚠️ Database connection failed: {str(e)}")
        return None

supabase: Client = get_supabase_client()
#pdf validate
def validate_pdf_file(uploaded_file):
    if uploaded_file is None:
        return False, "No file uploaded"
    
    if uploaded_file.type != "application/pdf":
        return False, "File must be a PDF"
    
    if uploaded_file.size > 20 * 1024 * 1024:
        return False, "File size exceeds 20MB limit"
    
    return True, "Valid"

def extract_pdf_text(uploaded_file):
    try:
        is_valid, message = validate_pdf_file(uploaded_file)
        if not is_valid:
            raise Exception(message)
        
        pdf_bytes = uploaded_file.read()
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        text = "".join([page.get_text() + "\n" for page in doc])
        doc.close()
        
        if not text.strip():
            raise Exception("PDF appears to be empty or contains only images")
        
        return text
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise Exception(f"PDF extraction error: {str(e)}")

def parse_resume(text):
    if not nlp:
        raise Exception("NLP model not available")
    
    if not text or len(text.strip()) < 100:
        raise Exception("Resume text is too short or empty")
    
    skills_list = [
        'Python', 'Java', 'JavaScript', 'SQL', 'AWS', 'Docker', 'Kubernetes',
        'React', 'Node.js', 'Django', 'Flask', 'PostgreSQL', 'MongoDB',
        'Machine Learning', 'Data Science', 'Git', 'CI/CD', 'Agile', 'Scrum',
        'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'TypeScript', 
        'Angular', 'Vue.js', 'Spring', 'TensorFlow', 'PyTorch', 'Pandas',
        'NumPy', 'Scikit-learn', 'Spark', 'Hadoop', 'Kafka', 'Redis',
        'Elasticsearch', 'GraphQL', 'REST API', 'Microservices', 'HTML',
        'CSS', 'Bootstrap', 'Tailwind', 'Azure', 'GCP', 'Jenkins', 'Ansible'
    ]
    
    text_lower = text.lower()
    skills = []
    seen_skills = set()
    
    for skill in skills_list:
        if skill.lower() in text_lower and skill.lower() not in seen_skills:
            skills.append(skill)
            seen_skills.add(skill.lower())
    
    experience_patterns = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'experience[:\s]+(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s+in\s+',
        r'worked\s+for\s+(\d+)\+?\s*years?'
    ]
    
    experience_years = 0
    for pattern in experience_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            exp_values = [int(m) for m in matches if int(m) <= 50]
            if exp_values:
                experience_years = max(experience_years, max(exp_values))
    
    projects_section = extract_section(text, ['project', 'projects'])
    education_section = extract_section(text, ['education', 'academic', 'qualification'])
    
    return {
        'skills': skills, 
        'experience_years': experience_years,
        'projects_section': projects_section,
        'education_section': education_section
    }

def extract_section(text, keywords):
    if not text:
        return ""
    
    lines = text.split('\n')
    section_text = ""
    capturing = False
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        if any(kw in line_lower for kw in keywords):
            capturing = True
            continue
        
        if capturing and line_lower and line.strip().isupper() and len(line.strip()) < 50:
            break
            
        if capturing:
            section_text += line + "\n"
    
    return section_text.strip()
#projects and skills listed are same
def validate_projects(projects_section, skills):
    if not projects_section or not skills:
        return 0, []
    
    projects_lower = projects_section.lower()
    verified_skills = [s for s in skills if s.lower() in projects_lower]
    verification_rate = len(verified_skills) / len(skills) if skills else 0
    
    return verification_rate, verified_skills
#10 cg wali bkd
def validate_education(education_section, jd_education):
    score = 0
    penalties = []
    
    if not education_section:
        return 0, penalties
    
    edu_lower = education_section.lower()
    jd_lower = jd_education.lower() if jd_education else ""
    
    degrees = ['bachelor', 'b.tech', 'b.e.', 'bsc', 'master', 'm.tech', 'm.sc', 'phd', 'mba']
    jd_degrees = [d for d in degrees if d in jd_lower]
    resume_degrees = [d for d in degrees if d in edu_lower]
    
    if jd_degrees and resume_degrees:
        if any(jd_deg in resume_degrees for jd_deg in jd_degrees):
            score += 15
        else:
            score += 5  
    elif resume_degrees and not jd_degrees:
        score += 10  
    
    cgpa_pattern = r'(?:cgpa|gpa|grade)[:\s]*(\d+\.?\d*)\s*(?:/\s*(\d+\.?\d*))?'
    cgpa_matches = re.findall(cgpa_pattern, edu_lower)
    
    for match in cgpa_matches:
        try:
            cgpa_value = float(match[0])
            max_scale = float(match[1]) if match[1] else 10.0
            
            if max_scale <= 0:
                continue
            
            if cgpa_value > max_scale:
                penalties.append(f"Invalid CGPA: {cgpa_value}/{max_scale}")
                score -= 5
            elif cgpa_value == max_scale:
                penalties.append(f"Perfect CGPA claimed: {cgpa_value}/{max_scale}")
                score -= 2
            elif cgpa_value > (max_scale * 0.95):
                penalties.append(f"Suspiciously high CGPA: {cgpa_value}/{max_scale}")
                score -= 1
        except (ValueError, ZeroDivisionError):
            continue
    
    fields = [
        'computer science', 'software engineering', 'information technology', 
        'electrical engineering', 'electronics', 'data science', 'artificial intelligence'
    ]
    
    if jd_lower:
        jd_fields = [f for f in fields if f in jd_lower]
        resume_fields = [f for f in fields if f in edu_lower]
        
        if jd_fields and resume_fields:
            if any(jf in resume_fields for jf in jd_fields):
                score += 15
            else:
                score += 5
    
    return max(0, score), penalties
#penalty system
def check_plagiarism(resume_text, reference_corpus=None):
    if not reference_corpus or len(reference_corpus) == 0:
        return 0, "No reference data"
    
    try:
        if not resume_text or not resume_text.strip():
            return 0, "Empty resume"
        
        corpus = [resume_text] + reference_corpus
        
        if len(corpus) < 2:
            return 0, "Insufficient corpus"
        
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=1000)
        tfidf_matrix = vectorizer.fit_transform(corpus)
        
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        max_similarity = float(np.max(similarities)) if similarities.size > 0 else 0.0
        plagiarism_score = round(max_similarity * 100, 2)
        
        return plagiarism_score, "Checked"
        
    except Exception as e:
        logger.error(f"Plagiarism check error: {e}")
        return 0, f"Error: {str(e)}"

def calculate_ats_score(resume_text, job_description, jd_education="", reference_corpus=None):
    if not resume_text or not job_description:
        raise Exception("Resume text and job description are required")
    
    if len(resume_text.strip()) < 100:
        raise Exception("Resume text is too short")
    
    if len(job_description.strip()) < 50:
        raise Exception("Job description is too short")
    
    try:
        parsed = parse_resume(resume_text)
    except Exception as e:
        raise Exception(f"Resume parsing failed: {str(e)}")
    
    score = 0
    feedback = []
    penalties = []
    
    jd_lower = job_description.lower()
    
    matched_skills = [s for s in parsed['skills'] if s.lower() in jd_lower]
    if parsed['skills']:
        skills_score = (len(matched_skills) / len(parsed['skills'])) * 40
        score += skills_score
        feedback.append(f"Matched {len(matched_skills)}/{len(parsed['skills'])} skills")
    else:
        feedback.append("No skills detected")
    
    exp_match = re.search(r'(\d+)\+?\s*years?', job_description.lower())
    required_exp = int(exp_match.group(1)) if exp_match else 2
    
    if required_exp == 0:
        required_exp = 1
    
    if parsed['experience_years'] >= required_exp:
        score += 20
        feedback.append(f"Experience: {parsed['experience_years']} years (meets requirement)")
    elif parsed['experience_years'] > 0:
        exp_score = min((parsed['experience_years'] / required_exp) * 20, 20)
        score += exp_score
        feedback.append(f"Experience: {parsed['experience_years']} years (below requirement)")
    else:
        feedback.append("No experience detected")
    
    project_verification, verified_skills = validate_projects(parsed['projects_section'], parsed['skills'])
    project_score = project_verification * 10
    score += project_score
    
    if project_verification > 0.7:
        feedback.append(f"Projects verified {len(verified_skills)} skills")
    elif project_verification > 0.3:
        feedback.append(f"Projects partially verified skills")
    else:
        feedback.append("Projects don't demonstrate claimed skills")
        penalties.append("Skills not verified in projects (-3 points)")
        score -= 3
    
    education_score, edu_penalties = validate_education(parsed['education_section'], jd_education)
    score += education_score
    penalties.extend(edu_penalties)
    
    if education_score > 20:
        feedback.append("Education strongly matches requirements")
    elif education_score > 10:
        feedback.append("Education partially matches requirements")
    else:
        feedback.append("Education doesn't match requirements")
    
    plagiarism_score = 0
    plag_status = "Not checked"
    
    if reference_corpus:
        plagiarism_score, plag_status = check_plagiarism(resume_text, reference_corpus)
        
        if plagiarism_score > 80:
            penalties.append(f"High plagiarism detected: {plagiarism_score}% (-20 points)")
            score -= 20
        elif plagiarism_score > 60:
            penalties.append(f"Moderate plagiarism detected: {plagiarism_score}% (-10 points)")
            score -= 10
        elif plagiarism_score > 40:
            penalties.append(f"Some plagiarism detected: {plagiarism_score}% (-5 points)")
            score -= 5
    
    feedback.append(f"Plagiarism check: {plagiarism_score}% similarity")
    
    if parsed['experience_years'] > 20:
        penalties.append("Unrealistic experience years (-10 points)")
        score -= 10
    
    for skill in parsed['skills'][:5]:
        count = resume_text.lower().count(skill.lower())
        if count > 15:
            penalties.append(f"Keyword stuffing detected: '{skill}' repeated {count} times (-5 points)")
            score -= 5
            break 
    
    final_score = max(0, min(score, 100))
    
    return {
        **parsed, 
        'score': round(final_score, 2),
        'matched_skills': matched_skills,
        'feedback': feedback,
        'penalties': penalties,
        'plagiarism_score': plagiarism_score
    }

def sanitize_input(text, max_length=500):
    if not text:
        return ""
    
    text = text.strip()[:max_length]
    text = re.sub(r'[<>"\';]', '', text)
    
    return text

def validate_email(email):
    if not email:
        return False
    
    email = email.strip().lower()
    email_pattern = r'^[a-zA-Z0-9._%+-]+@thapar\.edu$'
    
    return re.match(email_pattern, email) is not None

def validate_mobile(mobile):
    if not mobile:
        return False
    
    mobile_clean = re.sub(r'[\s\-\+()]', '', mobile)
    
    if len(mobile_clean) < 10 or len(mobile_clean) > 15:
        return False
    
    return mobile_clean.isdigit()

def register_participant(name, email, mobile):
    if not supabase:
        return str(uuid.uuid4())
    
    try:
        name = sanitize_input(name, 200)
        email = sanitize_input(email, 200).lower()
        mobile = sanitize_input(mobile, 20)
        
        if not name or len(name) < 3:
            raise Exception("Invalid name")
        
        if not validate_email(email):
            raise Exception("Invalid email")
        
        if not validate_mobile(mobile):
            raise Exception("Invalid mobile number")
        
        participant_id = str(uuid.uuid4())
        data = {
            'id': participant_id,
            'name': name,
            'email': email,
            'mobile': mobile
        }
        supabase.table('participants').insert(data).execute()
        return participant_id
    except Exception as e:
        logger.error(f"Registration error: {e}")
        st.error(f"Registration error: {str(e)}")
        return None

def check_participant_exists(email):
    if not supabase:
        return None
    
    try:
        email = sanitize_input(email, 200).lower()
        response = supabase.table('participants').select('*').eq('email', email).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Check error: {e}")
        st.error(f"Error checking participant: {str(e)}")
        return None

def save_participant_application(score, skills, experience_years, participant_id):
    if not supabase:
        return False
    
    try:
        if not participant_id:
            raise Exception("Invalid participant ID")
        
        if not isinstance(score, (int, float)) or score < 0 or score > 100:
            raise Exception("Invalid score")
        
        data = {
            'participant_id': participant_id,
            'score': float(score),
            'skills_count': len(skills) if isinstance(skills, list) else 0,
            'experience_years': int(experience_years) if experience_years else 0
        }
        supabase.table('applications').insert(data).execute()
        return True
    except Exception as e:
        logger.error(f"Save error: {e}")
        st.error(f"Error saving application: {str(e)}")
        return False

def get_participant_upload_count(participant_id):
    if not supabase or not participant_id:
        return 0
    
    try:
        response = supabase.table('applications').select('id').eq('participant_id', participant_id).execute()
        return len(response.data) if response.data else 0
    except Exception as e:
        logger.error(f"Count error: {e}")
        return 0

def get_participant_scores(participant_id):
    if not supabase or not participant_id:
        return pd.DataFrame()
    
    try:
        response = supabase.table('applications').select('*').eq('participant_id', participant_id).order('created_at', desc=True).execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Scores error: {e}")
        return pd.DataFrame()

def get_leaderboard():
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table('applications').select('participant_id, score, skills_count, experience_years').execute()
        
        if not response.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(response.data)
        
        df = df.loc[df.groupby('participant_id')['score'].idxmax()]
        df = df.sort_values('score', ascending=False).reset_index(drop=True)
        df['rank'] = range(1, len(df) + 1)
        
        participants = supabase.table('participants').select('id, email').execute()
        
        if participants.data:
            participants_df = pd.DataFrame(participants.data)
            df = df.merge(participants_df, left_on='participant_id', right_on='id', how='left')
            df = df.rename(columns={'experience_years': 'experience'})
            return df[['rank', 'email', 'score', 'skills_count', 'experience']].head(10)
        
        return df.head(10)
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        return pd.DataFrame()

def get_competition_stats():
    if not supabase:
        return None
    
    try:
        apps = supabase.table('applications').select('score, experience_years').execute()
        participants = supabase.table('participants').select('id').execute()
        
        if not apps.data or not participants.data:
            return None
        
        df = pd.DataFrame(apps.data)
        
        stats = {
            'total_participants': len(participants.data),
            'avg_score': float(df['score'].mean()),
            'top_score': float(df['score'].max()),
            'high_scorers': int(len(df[df['score'] >= 80])),
            'score_distribution': [
                {'range': '0-60%', 'count': int(len(df[df['score'] < 60]))},
                {'range': '60-80%', 'count': int(len(df[(df['score'] >= 60) & (df['score'] < 80)]))},
                {'range': '80-100%', 'count': int(len(df[df['score'] >= 80]))}
            ],
            'experience_distribution': [
                {'range': '0-2 years', 'count': int(len(df[df['experience_years'] <= 2]))},
                {'range': '3-5 years', 'count': int(len(df[(df['experience_years'] >= 3) & (df['experience_years'] <= 5)]))},
                {'range': '6-8 years', 'count': int(len(df[(df['experience_years'] >= 6) & (df['experience_years'] <= 8)]))},
                {'range': '8+ years', 'count': int(len(df[df['experience_years'] > 8]))}
            ]
        }
        
        return stats
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return None