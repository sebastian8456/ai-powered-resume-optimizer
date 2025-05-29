from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Header
from dotenv import load_dotenv
from openai import OpenAI
from backend.APIs.open_ai import generate_resume
from backend.classes.resume import Resume
from backend.classes.job_posting import JobPosting
from backend.classes.suggestion import Suggestion
from backend.classes.user_create import UserCreate
from backend.classes.user_login import UserLogin
from sqlalchemy import Column, Integer, String, create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import requests
import PyPDF2
import io
import os
import bcrypt
import secrets

app = FastAPI()
load_dotenv()

# Make sure that CORS is properly configured
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React default port
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

## Create tables if they don't exist
Base.metadata.create_all(bind=engine)

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
        # Get the resume text
        resume_text = resume.text
        
        client = OpenAI(api_key=os.getenv("open_ai_secret"))
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
            model="gpt-4o-mini-2024-07-18",
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