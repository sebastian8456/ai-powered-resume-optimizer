from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Header, Query
from dotenv import load_dotenv
from openai import OpenAI
from backend.APIs.open_ai import generate_resume
from backend.classes.resume import Resume
from backend.classes.job_posting import JobPosting
from backend.classes.suggestion import Suggestion
from backend.classes.user_create import UserCreate
from backend.classes.user_login import UserLogin
from sqlalchemy import Column, Integer, String, DateTime, create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import requests
import PyPDF2
import io
import os
import bcrypt
import secrets
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch
from fastapi.responses import StreamingResponse
import re
import httpx
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from datetime import datetime

app = FastAPI()
load_dotenv()

# Make sure that CORS is properly configured
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:3000", "http://localhost:8000"],  # Your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up database
SQLALCHEMY_DATABASE_URL = "sqlite:///./resume-checker.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


#### DATABASE TABLES ####
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    session_token = Column(String, nullable=True)

class ResumeDB(Base):
    __tablename__ = "Resumes"
    id = Column(Integer, primary_key=True)
    text = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

class SuggestionDB(Base):
    __tablename__ = "Suggestions"
    id = Column(Integer, primary_key=True)
    suggestion = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

class JobPostingDB(Base):
    __tablename__ = "Job_Postings"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    company = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

class SavedJob(Base):
    __tablename__ = "saved_jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    organization = Column(String)
    location = Column(String)
    url = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

## Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# FOR JOBMATCH
class ResumeInput(BaseModel):
    text: str

class SavedJobOut(BaseModel):
    id: int
    title: str
    organization: str
    location: str
    url: str
    timestamp: datetime

    class Config:
        orm_mode = True

#### AUTHENTICATION ####

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.replace("Bearer ", "")
    
    with SessionLocal() as session:
        user = session.query(UserDB).filter(UserDB.session_token == token).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user

# Keyword Matching Helpers
kw_model = KeyBERT(SentenceTransformer("all-MiniLM-L6-v2"))

def extract_skills_keywords(text: str) -> List[str]:
    match = re.search(r"(?i)skills?\s*:\s*(.*?)(?=(\n[a-zA-Z ]+:|$))", text, re.DOTALL)
    if not match:
        return []
    skills_block = match.group(1)
    lines = skills_block.strip().split("\n")
    section_keywords = [line.split(":")[0].strip().lower() for line in lines if ":" in line and 1 <= len(line.split(":")[0].split()) <= 4]
    return section_keywords

def extract_summary_and_experience(text: str) -> str:
    summary_match = re.search(r"(?i)summary:\s*(.*?)(?=(\n[a-zA-Z ]+:|skills:))", text, re.DOTALL)
    experience_match = re.search(r"(?i)professional experience:\s*(.*)", text, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""
    experience = experience_match.group(1).strip() if experience_match else ""
    return f"{summary} {experience}"

def extract_keywords(text: str, max_keywords: int = 25) -> List[str]:
    keyword_candidates = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 3), stop_words='english', top_n=max_keywords * 2)
    filtered = [phrase.strip().lower() for phrase, _ in keyword_candidates if 2 <= len(phrase) <= 40 and len(phrase.split()) <= 4 and not any(x in phrase for x in {"etc", "responsible", "tools", "languages"})]
    seen, keywords = set(), []
    for kw in filtered:
        if kw not in seen:
            seen.add(kw)
            keywords.append(kw)
    return keywords[:max_keywords]

async def search_usajobs(keywords: List[str]):
    query = " OR ".join(keywords[:1])
    url = f"https://data.usajobs.gov/api/search?Keyword={query}&ResultsPerPage=20"
    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": os.getenv("USAJOBS_USER_AGENT"),
        "Authorization-Key": os.getenv("USAJOBS_API_KEY"),
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="USAJobs API error")
        return response.json()

# Job Matching Endpoints
@app.post("/match-jobs/")
async def match_jobs(resume: ResumeInput, save_results: bool = Query(False), current_user: UserDB = Depends(get_current_user)):
    skills_keywords = extract_skills_keywords(resume.text)
    text_block = extract_summary_and_experience(resume.text)
    phrase_keywords = extract_keywords(text_block)
    all_keywords = list(dict.fromkeys(skills_keywords + phrase_keywords))
    irrelevant_terms = {"tools", "languages", "team", "experience", "responsible"}
    cleaned_keywords = [kw for kw in all_keywords if kw.lower() not in irrelevant_terms][:7]
    if not cleaned_keywords:
        full_keywords = extract_keywords(resume.text, max_keywords=15)
        cleaned_keywords = full_keywords[:7] if full_keywords else [resume.text.strip()]

    jobs_data = await search_usajobs(cleaned_keywords)
    matched_jobs = []
    with SessionLocal() as session:
        for job in jobs_data.get("SearchResult", {}).get("SearchResultItems", []):
            job_info = {
                "title": job["MatchedObjectDescriptor"]["PositionTitle"],
                "organization": job["MatchedObjectDescriptor"]["OrganizationName"],
                "location": job["MatchedObjectDescriptor"]["PositionLocation"][0]["LocationName"],
                "url": job["MatchedObjectDescriptor"]["PositionURI"],
            }
            matched_jobs.append(job_info)
            if save_results:
                new_job = SavedJob(**job_info)
                session.add(new_job)
        if save_results:
            session.commit()

    return {"keywords": cleaned_keywords, "jobs": matched_jobs}

@app.get("/saved-jobs/", response_model=List[SavedJobOut])
async def get_saved_jobs(current_user: UserDB = Depends(get_current_user)):
    with SessionLocal() as session:
        jobs = session.query(SavedJob).order_by(SavedJob.timestamp.desc()).limit(20).all()
        return jobs
    
#### AUTHENTICATION ENDPOINTS ####
@app.post("/register")
async def register(user: UserCreate):
    with SessionLocal() as session:
        # Check if user exists
        existing_user = session.query(UserDB).filter(UserDB.username == user.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create new user
        hashed_pw = hash_password(user.password)
        db_user = UserDB(username=user.username, hashed_password=hashed_pw)
        session.add(db_user)
        session.commit()
        return {"message": "User created successfully"}

@app.post("/login")
async def login(user: UserLogin):
    with SessionLocal() as session:
        db_user = session.query(UserDB).filter(UserDB.username == user.username).first()
        if not db_user or not verify_password(user.password, db_user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        db_user.session_token = session_token
        session.commit()
        
        return {"access_token": session_token, "message": "Login successful"}

@app.post("/logout")
async def logout(current_user: UserDB = Depends(get_current_user)):
    with SessionLocal() as session:
        user = session.query(UserDB).filter(UserDB.id == current_user.id).first()
        user.session_token = None
        session.commit()
        return {"message": "Logged out successfully"}


#### HTTP REQUESTS ####

@app.get("/")
async def root():
    return {"message": "Hello, please enter a valid endpoint: /resumes, /suggestions, or /job-postings"}

# Resume requests
async def add_resume(resume: Resume, current_user: UserDB = Depends(get_current_user)):
    with SessionLocal() as session:
        resume_data = resume.dict()
        resume_data['user_id'] = current_user.id
        db_resume = ResumeDB(**resume_data)
        session.add(db_resume)
        session.commit()
        session.refresh(db_resume)
        return db_resume

@app.delete("/resume")
async def del_resume(resume_id: int, current_user: UserDB = Depends(get_current_user)):
    with SessionLocal() as session:
        resume = session.query(ResumeDB).filter(
            ResumeDB.id == resume_id, 
            ResumeDB.user_id == current_user.id
        ).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        session.delete(resume)
        session.commit()
        return {"message": "Resume deleted"}

@app.get("/resumes", response_model=list[Resume])
async def get_resume(current_user: UserDB = Depends(get_current_user)):
    with SessionLocal() as session:
        resumes = session.query(ResumeDB).filter(ResumeDB.user_id == current_user.id).all()
        return resumes

# Generate a new resume using OpenAI
@app.get("/create-resume")
async def create_resume(current_user: UserDB = Depends(get_current_user)):
    resume = generate_resume(os.getenv("open_ai_secret"))
    return {"New resume: ": resume}


# Suggestion requests
@app.post("/suggestion", response_model=Suggestion)
async def add_suggestion(suggestion: Suggestion, current_user: UserDB = Depends(get_current_user)):
    with SessionLocal() as session:
        suggestion_data = suggestion.dict()
        suggestion_data['user_id'] = current_user.id
        db_suggestion = SuggestionDB(**suggestion_data)
        session.add(db_suggestion)
        session.commit()
        session.refresh(db_suggestion)
        return db_suggestion

@app.delete("/suggestion")
async def del_suggestion(suggestion_id: int, current_user: UserDB = Depends(get_current_user)):
    with SessionLocal() as session:
        suggestion = session.query(SuggestionDB).filter(
            SuggestionDB.id == suggestion_id,
            SuggestionDB.user_id == current_user.id
        ).first()
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        session.delete(suggestion)
        session.commit()
        return {"message": "Suggestion deleted"}

@app.get("/suggestions", response_model=list[Suggestion])
async def get_suggestions(current_user: UserDB = Depends(get_current_user)):
    with SessionLocal() as session:
        suggestions = session.query(SuggestionDB).filter(SuggestionDB.user_id == current_user.id).all()
        return suggestions


# Job posting requests w/ JobPosting objects
@app.post("/job-posting", response_model=JobPosting)
async def add_job_posting(job_posting: JobPosting, current_user: UserDB = Depends(get_current_user)):
    with SessionLocal() as session:
        job_data = job_posting.dict()
        job_data['user_id'] = current_user.id
        db_job_posting = JobPostingDB(**job_data)
        session.add(db_job_posting)
        session.commit()
        session.refresh(db_job_posting)
        return db_job_posting

@app.delete("/job-posting")
async def delete_job_posting(job_posting_id: int, current_user: UserDB = Depends(get_current_user)):
    with SessionLocal() as session:
        job_posting = session.query(JobPostingDB).filter(
            JobPostingDB.id == job_posting_id,
            JobPostingDB.user_id == current_user.id
        ).first()
        if not job_posting:
            raise HTTPException(status_code=404, detail="Job Posting not found")
        session.delete(job_posting)
        session.commit()
        return {"message": "Job posting deleted"}

@app.get("/job-postings", response_model=list[JobPosting])
async def get_job_postings(current_user: UserDB = Depends(get_current_user)):
    with SessionLocal() as session:
        job_postings = session.query(JobPostingDB).filter(JobPostingDB.user_id == current_user.id).all()
        return job_postings

    
# Additional resume requests
    
@app.post("/optimize-resume")
async def optimize_resume(resume: Resume, current_user: UserDB = Depends(get_current_user)):
    try:
        resume_text = resume.text

        api_key = os.getenv("open_ai_secret")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not found in environment variables")

        client = OpenAI(api_key=api_key)

        prompt = f"""Analyze this resume and provide specific, actionable suggestions for improvement. Use markdown formatting:
- Use **bold** for emphasis
- Use ## for section headers
- Use bullet points (-) for lists
- Add a blank line after each section

Format your response as follows:

## KEY STRENGTHS
- List 3 main strengths of the resume

## AREAS FOR IMPROVEMENT
- List 3 specific areas that need enhancement

## SECTION-SPECIFIC SUGGESTIONS

### Summary/Objective
- Provide 2-3 specific suggestions

### Experience
- Provide 2-3 specific suggestions for each role
- Focus on impact and metrics

### Education
- Provide 1-2 specific suggestions

### Skills
- Provide 2-3 specific suggestions for better presentation

## OPTIMIZED VERSION
[Provide a clean, optimized version of the resume with the suggested improvements implemented]

Resume to analyze:
{resume_text}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )

        suggestions = response.choices[0].message.content

        return {
            "suggestions": suggestions,
            "optimized_resume": resume_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), current_user: UserDB = Depends(get_current_user)):
    try:
        # Read the uploaded file
        contents = await file.read()
        
        # Check if it's a PDF file
        if file.content_type == "application/pdf":
            # Create a PDF reader object
            pdf_file = io.BytesIO(contents)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from all pages
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # Create a new resume object and save to database
            with SessionLocal() as session:
                db_resume = ResumeDB(text=text, user_id=current_user.id)
                session.add(db_resume)
                session.commit()
                session.refresh(db_resume)
                return db_resume
        else:
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()

        from fastapi.responses import StreamingResponse
import io
from fpdf import FPDF

# Export Resume as PDF
@app.post("/export-resume")
def export_resume(resume: Resume):
    try:
        if not resume.text or not resume.text.strip():
            raise HTTPException(status_code=400, detail="Resume content is empty.")

        from io import BytesIO
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        pdf.setFont("Helvetica", 12)

        top = 750
        line_height = 15
        for i, line in enumerate(resume.text.split('\n')):
            y = top - i * line_height
            if y < 40:
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                top = 750
                y = top
            pdf.drawString(40, y, line)

        pdf.save()
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=resume.pdf"}
        )

    except Exception:
        import traceback
        print("Export Resume Error:\n", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to export resume.")