import pymupdf
import spacy
import re
import streamlit as st
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
import uuid

@st.cache_resource
def load_nlp():
    try:
        return spacy.load("en_core_web_sm") 
    except:
        return None

nlp = load_nlp()

@st.cache_resource
def get_supabase_client():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        return None

supabase: Client = get_supabase_client()

def extract_pdf_text(uploaded_file):
    try:
        pdf_bytes = uploaded_file.read()
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        text = "".join([page.get_text() + "\n" for page in doc])
        doc.close()
        return text
    except Exception as e:
        raise Exception(f"pdf extraction error: {str(e)}")

def parse_resume(text):
    if not nlp:
        raise Exception("nlp error")
    
    skills_list = ['Python', 'Java', 'JavaScript', 'SQL', 'AWS', 'Docker', 'Kubernetes',
                   'React', 'Node.js', 'Django', 'Flask', 'PostgreSQL', 'MongoDB',
                   'Machine Learning', 'Data Science', 'Git', 'CI/CD', 'Agile', 'Scrum']
    
    skills = list(dict.fromkeys([s for s in skills_list if s.lower() in text.lower()]))
    experience_years = max([int(m) for m in re.findall(r'(\d+)\+?\s*years?', text.lower())] or [0])
    
    return {'skills': skills, 'experience_years': experience_years}
def calculate_ats_score(resume_text, job_description):
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
    try:
        if not supabase:
            return None
        response = supabase.table('participants').select('*').eq('email', email).execute()
        return response.data[0] if response.data else None
    except:
        return None
def register_participant(name, email, mobile):
    try:
        if not supabase:
            return str(uuid.uuid4())
        data = {
            'id': str(uuid.uuid4()),
            'name': name,
            'email': email,
            'mobile': mobile,
            'upload_count': 0,
            'view_count': 0,
            'registered_at': datetime.now().isoformat()
        }
        response = supabase.table('participants').insert(data).execute()
        return data['id']
    except:
        return str(uuid.uuid4())
def save_participant_application(score, skills, experience, participant_id):
    try:
        if not supabase:
            return
        # saving app
        data = {
            'score': float(score),
            'skills': skills,
            'skills_count': len(skills),
            'experience_years': float(experience),
            'participant_id': participant_id,
            'submitted_at': datetime.now().isoformat()
        }
        supabase.table('applications').insert(data).execute()
        # upload cnt ++
        response = supabase.table('participants').select('upload_count').eq('id', participant_id).execute()
        if response.data:
            current_count = response.data[0]['upload_count']
            supabase.table('participants').update({'upload_count': current_count + 1}).eq('id', participant_id).execute()
        
    except Exception as e:
        raise Exception(f"Submission error: {str(e)}")

def get_participant_upload_count(participant_id):
    try:
        if not supabase:
            return 0
        response = supabase.table('participants').select('upload_count').eq('id', participant_id).execute()
        return response.data[0]['upload_count'] if response.data else 0
    except:
        return 0

def get_participant_view_count(participant_id):
    try:
        if not supabase:
            return 0
        response = supabase.table('participants').select('view_count').eq('id', participant_id).execute()
        return response.data[0]['view_count'] if response.data else 0
    except:
        return 0

def increment_view_count(participant_id):
    """Increment view count when participant checks scores"""
    try:
        if not supabase:
            return
        response = supabase.table('participants').select('view_count').eq('id', participant_id).execute()
        if response.data:
            current_count = response.data[0]['view_count']
            supabase.table('participants').update({'view_count': current_count + 1}).eq('id', participant_id).execute()
    except:
        pass

def get_participant_scores(participant_id):
    """scores for specific participant"""
    try:
        if not supabase:
            return pd.DataFrame()
        
        response = supabase.table('applications')\
            .select('*')\
            .eq('participant_id', participant_id)\
            .order('submitted_at', desc=True)\
            .execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def get_leaderboard():
    """top 10 participants by score"""
    try:
        if not supabase:
            return pd.DataFrame()
        
        # get all applications with participant details
        response = supabase.table('applications')\
            .select('*, participants(email, name)')\
            .execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # extract email from nested participants object
            df['email'] = df['participants'].apply(lambda x: x['email'] if x else 'N/A')
            df['name'] = df['participants'].apply(lambda x: x['name'] if x else 'N/A')
            
            # get best score per participant
            df = df.loc[df.groupby('participant_id')['score'].idxmax()]
            df = df.sort_values('score', ascending=False).head(10)
            df['rank'] = range(1, len(df) + 1)
            df = df.rename(columns={'experience_years': 'experience'})
            
            return df[['rank', 'participant_id', 'email', 'name', 'score', 'skills_count', 'experience']]
        
        return pd.DataFrame()
    except Exception as e:
        # exception handler
        try:
            # get applications
            apps_response = supabase.table('applications').select('*').execute()
            # get participants
            parts_response = supabase.table('participants').select('*').execute()
            if apps_response.data and parts_response.data:
                df_apps = pd.DataFrame(apps_response.data)
                df_parts = pd.DataFrame(parts_response.data)
                # merge to get emails
                df = df_apps.merge(df_parts[['id', 'email', 'name']], 
                                  left_on='participant_id', 
                                  right_on='id', 
                                  how='left')
                # get best score per participant
                df = df.loc[df.groupby('participant_id')['score'].idxmax()]
                df = df.sort_values('score', ascending=False).head(10)
                df['rank'] = range(1, len(df) + 1)
                df = df.rename(columns={'experience_years': 'experience'})
                
                return df[['rank', 'participant_id', 'email', 'name', 'score', 'skills_count', 'experience']]
            
            return pd.DataFrame()
        except:
            return pd.DataFrame()

@st.cache_data(ttl=60)
def get_competition_stats():
    """Get overall competition statistics (unique participants only)"""
    try:
        if not supabase:
            return None
        
        # get unique participants count
        participants_response = supabase.table('participants').select('id').execute()
        total_participants = len(participants_response.data) if participants_response.data else 0
        # get applications
        response = supabase.table('applications').select('*').execute()
        if not response.data:
            return None
        df = pd.DataFrame(response.data)
        # get best score per participant for stats
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