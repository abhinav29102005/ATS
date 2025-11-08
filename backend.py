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


@st.cache_resource
def load_nlp():
    """load spacy nlp model with error handling"""
    try:
        import en_core_web_sm
        return en_core_web_sm.load()
    except:
        try:
            return spacy.load("en_core_web_sm")
        except:
            st.error("⚠️ nlp model not available. please install: python -m spacy download en_core_web_sm")
            return None


nlp = load_nlp()


@st.cache_resource
def get_supabase_client():
    """initialize supabase client with error handling"""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError as e:
        st.error(f"⚠️ supabase secret missing: {e}")
        return None
    except Exception as e:
        st.error(f"⚠️ supabase connection failed: {e}")
        return None


supabase: Client = get_supabase_client()


def extract_pdf_text(uploaded_file):
    """extract text from uploaded pdf file"""
    try:
        pdf_bytes = uploaded_file.read()
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        text = "".join([page.get_text() + "\n" for page in doc])
        doc.close()
        return text
    except Exception as e:
        st.error(f"pdf extraction error: {str(e)}")
        raise Exception(f"pdf extraction error: {str(e)}")


def parse_resume(text):
    """parse resume text and extract key information"""
    if not nlp:
        st.error("⚠️ nlp model not loaded. cannot parse resume.")
        raise Exception("nlp error")
    
    # list of technical skills to search for
    skills_list = ['Python', 'Java', 'JavaScript', 'SQL', 'AWS', 'Docker', 'Kubernetes',
                   'React', 'Node.js', 'Django', 'Flask', 'PostgreSQL', 'MongoDB',
                   'Machine Learning', 'Data Science', 'Git', 'CI/CD', 'Agile', 'Scrum',
                   'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'TypeScript', 
                   'Angular', 'Vue.js', 'Spring', 'TensorFlow', 'PyTorch', 'Pandas',
                   'NumPy', 'Scikit-learn', 'Spark', 'Hadoop', 'Kafka', 'Redis',
                   'Elasticsearch', 'GraphQL', 'REST API', 'Microservices']
    
    # extract skills from resume text
    skills = list(dict.fromkeys([s for s in skills_list if s.lower() in text.lower()]))
    
    # extract years of experience
    experience_years = max([int(m) for m in re.findall(r'(\d+)\+?\s*years?', text.lower())] or [0])
    
    # extract projects and education sections
    projects_section = extract_section(text, ['project', 'projects'])
    education_section = extract_section(text, ['education', 'academic', 'qualification'])
    
    return {
        'skills': skills, 
        'experience_years': experience_years,
        'projects_section': projects_section,
        'education_section': education_section
    }


def extract_section(text, keywords):
    """extract specific sections from resume based on keywords"""
    lines = text.split('\n')
    section_text = ""
    capturing = False
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # start capturing when keyword is found
        if any(kw in line_lower for kw in keywords):
            capturing = True
            continue
        
        # stop capturing when new section header is found
        if capturing and line_lower and line.isupper() and len(line.strip()) < 50:
            break
            
        if capturing:
            section_text += line + "\n"
    
    return section_text


def validate_projects(projects_section, skills):
    """check if skills are actually mentioned in projects"""
    if not projects_section or not skills:
        return 0, []
    
    projects_lower = projects_section.lower()
    verified_skills = [s for s in skills if s.lower() in projects_lower]
    verification_rate = len(verified_skills) / len(skills) if skills else 0
    
    return verification_rate, verified_skills


def validate_education(education_section, jd_education):
    """validate education details and check for unrealistic claims"""
    score = 0
    penalties = []
    
    if not education_section:
        return 0, penalties
    
    edu_lower = education_section.lower()
    jd_lower = jd_education.lower() if jd_education else ""
    
    # check for degree match
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
    
    # detect unrealistic cgpa claims
    cgpa_match = re.findall(r'(?:cgpa|gpa|grade)[:\s]*(\d+\.?\d*)\s*(?:/\s*(\d+\.?\d*))?', edu_lower)
    
    for match in cgpa_match:
        cgpa_value = float(match[0])
        max_scale = float(match[1]) if match[1] else 10.0
        
        # check for impossible values
        if cgpa_value > max_scale:
            penalties.append(f"invalid cgpa: {cgpa_value}/{max_scale}")
            score -= 5
        # check for suspiciously perfect scores
        elif cgpa_value == max_scale:
            penalties.append(f"perfect cgpa claimed: {cgpa_value}/{max_scale}")
            score -= 2
        # check for unrealistic high scores
        elif cgpa_value > (max_scale * 0.95):
            penalties.append(f"suspiciously high cgpa: {cgpa_value}/{max_scale}")
            score -= 1
    
    # check for field of study match
    fields = ['computer science', 'software engineering', 'information technology', 
              'electrical engineering', 'electronics', 'data science', 'artificial intelligence']
    
    if jd_lower:
        jd_fields = [f for f in fields if f in jd_lower]
        resume_fields = [f for f in fields if f in edu_lower]
        
        if jd_fields and resume_fields:
            if any(jf in resume_fields for jf in jd_fields):
                score += 15
            else:
                score += 5
    
    return max(0, score), penalties


def check_plagiarism(resume_text, reference_corpus=[]):
    """check for plagiarism using cosine similarity"""
    if not reference_corpus:
        return 0, "no reference data"
    
    try:
        corpus = [resume_text] + reference_corpus
        
        # vectorize text using tfidf
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(corpus)
        
        # calculate cosine similarity
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        max_similarity = np.max(similarities) if similarities.size > 0 else 0
        plagiarism_score = round(max_similarity * 100, 2)
        
        return plagiarism_score, "checked"
        
    except Exception as e:
        return 0, f"error: {str(e)}"


def calculate_ats_score(resume_text, job_description, jd_education="", reference_corpus=[]):
    """
    calculate ats score with following weightage:
    skills: 40%
    work experience: 20%
    projects: 10%
    education: 30%
    """
    parsed = parse_resume(resume_text)
    score = 0
    feedback = []
    penalties = []
    
    jd_lower = job_description.lower()
    
    # skills matching - 40%
    matched_skills = [s for s in parsed['skills'] if s.lower() in jd_lower]
    if parsed['skills']:
        skills_score = (len(matched_skills) / len(parsed['skills'])) * 40
        score += skills_score
        feedback.append(f"matched {len(matched_skills)}/{len(parsed['skills'])} skills")
    else:
        feedback.append("no skills detected")
    
    # work experience - 20%
    exp_match = re.search(r'(\d+)\+?\s*years?', job_description.lower())
    required_exp = int(exp_match.group(1)) if exp_match else 2
    
    if parsed['experience_years'] >= required_exp:
        score += 20
        feedback.append(f"experience: {parsed['experience_years']} years (meets requirement)")
    elif parsed['experience_years'] > 0:
        exp_score = (parsed['experience_years'] / required_exp) * 20
        score += exp_score
        feedback.append(f"experience: {parsed['experience_years']} years (below requirement)")
    else:
        feedback.append("no experience detected")
    
    # projects verification - 10%
    project_verification, verified_skills = validate_projects(parsed['projects_section'], parsed['skills'])
    project_score = project_verification * 10
    score += project_score
    
    if project_verification > 0.7:
        feedback.append(f"projects verified {len(verified_skills)} skills")
    elif project_verification > 0.3:
        feedback.append(f"projects partially verified skills")
    else:
        feedback.append("projects don't demonstrate claimed skills")
        penalties.append("skills not verified in projects (-3 points)")
        score -= 3
    
    # education match - 30%
    education_score, edu_penalties = validate_education(parsed['education_section'], jd_education)
    score += education_score
    penalties.extend(edu_penalties)
    
    if education_score > 20:
        feedback.append("education strongly matches requirements")
    elif education_score > 10:
        feedback.append("education partially matches requirements")
    else:
        feedback.append("education doesn't match requirements")
    
    # plagiarism check
    plagiarism_score, plag_status = check_plagiarism(resume_text, reference_corpus)
    
    if plagiarism_score > 80:
        penalties.append(f"high plagiarism detected: {plagiarism_score}% (-20 points)")
        score -= 20
    elif plagiarism_score > 60:
        penalties.append(f"moderate plagiarism detected: {plagiarism_score}% (-10 points)")
        score -= 10
    elif plagiarism_score > 40:
        penalties.append(f"some plagiarism detected: {plagiarism_score}% (-5 points)")
        score -= 5
    
    feedback.append(f"plagiarism check: {plagiarism_score}% similarity")
    
    # check for unrealistic claims
    if parsed['experience_years'] > 8:
        penalties.append("unrealistic experience years (-10 points)")
        score -= 10
    
    # check for keyword stuffing
    for skill in parsed['skills']:
        count = resume_text.lower().count(skill.lower())
        if count > 15:
            penalties.append(f"keyword stuffing detected: '{skill}' repeated {count} times (-5 points)")
            score -= 5
            break 
    
    # calculate final score
    final_score = max(0, min(score, 100))
    
    return {
        **parsed, 
        'score': round(final_score, 2),
        'matched_skills': matched_skills,
        'feedback': feedback,
        'penalties': penalties,
        'plagiarism_score': plagiarism_score
    }
