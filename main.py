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
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch
from fastapi.responses import StreamingResponse

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
        resume_text = resume.text

        client = OpenAI(api_key=os.getenv("open_ai_secret"))
        prompt = f"""
You're an expert resume editor. Analyze the following resume and return structured JSON with specific, actionable changes. Each suggestion should be a complete replacement or addition that can be directly applied to the resume. The response must be valid JSON with this exact structure:

{{
  "suggestions": {{
    "summary": [
      {{
        "original": "current text to replace (or empty string if adding new)",
        "improved": "improved version of the text"
      }}
    ],
    "experience": [
      {{
        "original": "current text to replace (or empty string if adding new)",
        "improved": "improved version of the text"
      }}
    ],
    "education": [
      {{
        "original": "current text to replace (or empty string if adding new)",
        "improved": "improved version of the text"
      }}
    ],
    "skills": [
      {{
        "original": "current text to replace (or empty string if adding new)",
        "improved": "improved version of the text"
      }}
    ],
    "other": [
      {{
        "original": "current text to replace (or empty string if adding new)",
        "improved": "improved version of the text"
      }}
    ]
  }}
}}

Resume to analyze:
{resume_text}

For each suggestion:
1. If replacing existing text, include both the original text and the improved version
2. If adding new content, use empty string for "original" and provide the new content in "improved"
3. Make each suggestion specific and actionable
4. Return ONLY the JSON object, no other text
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        # Parse the response to ensure it's valid JSON
        try:
            suggestions = response.choices[0].message.content
            # Clean the response to ensure it's valid JSON
            suggestions = suggestions.strip()
            if suggestions.startswith('```json'):
                suggestions = suggestions[7:]
            if suggestions.endswith('```'):
                suggestions = suggestions[:-3]
            suggestions = suggestions.strip()
            
            # Parse the JSON to validate it
            import json
            parsed_suggestions = json.loads(suggestions)
            return parsed_suggestions
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Raw response: {suggestions}")
            raise HTTPException(status_code=500, detail="Invalid response format from AI")
        
    except Exception as e:
        print(f"Error in optimize_resume: {str(e)}")
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

# Export resume
@app.post("/export-resume")
async def export_resume(updated_text: dict, current_user: UserDB = Depends(get_current_user)):
    try:
        print("Starting export-resume process...")
        text = updated_text.get("text")
        if not text:
            print("Error: No text provided in request")
            raise HTTPException(status_code=400, detail="Missing resume text")

        print("Creating PDF buffer...")
        # Create a PDF in memory
        buffer = io.BytesIO()
        canvas_obj = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        print("Setting up styles...")
        # Set up styles
        styles = getSampleStyleSheet()
        style = ParagraphStyle(
            'CustomStyle',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            spaceBefore=6,
            spaceAfter=6
        )

        print("Processing text...")
        # Split text into lines and create paragraphs
        y = height - inch  # Start from top of page
        for line in text.split('\n'):
            if line.strip():  # Skip empty lines
                try:
                    p = Paragraph(line, style)
                    p.wrapOn(canvas_obj, width - 2*inch, height)
                    p.drawOn(canvas_obj, inch, y)
                    y -= p.height + 6  # Move down for next paragraph

                    # If we're near the bottom of the page, start a new page
                    if y < inch:
                        canvas_obj.showPage()
                        y = height - inch
                except Exception as e:
                    print(f"Error processing line: {line}")
                    print(f"Error details: {str(e)}")
                    continue

        print("Saving canvas...")
        canvas_obj.save()
        buffer.seek(0)

        print("Returning PDF response...")
        # Return the PDF file
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=resume.pdf"
            }
        )

    except Exception as e:
        print(f"Error in export_resume: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
