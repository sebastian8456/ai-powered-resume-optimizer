from fastapi import FastAPI, HTTPException, UploadFile, File
from dotenv import load_dotenv
import requests
from backend.APIs.open_ai import *
from backend.classes.resume import *
from backend.classes.job_posting import *
from backend.classes.suggestion import *
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import io

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
class ResumeDB(Base):
    __tablename__ = "Resumes"
    id = Column(Integer, primary_key=True)
    text = Column(String)

class SuggestionDB(Base):
    __tablename__ = "Suggestions"
    id = Column(Integer, primary_key=True)
    suggestion = Column(String)

class JobPostingDB(Base):
    __tablename__ = "Job_Postings"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    company = Column(String)

## Create tables if they don't exist
Base.metadata.create_all(bind=engine)


#### HTTP REQUESTS ####

@app.get("/")
async def root():
    return {"message": "Hello, please enter a valid endpoint: /resumes, /suggestions, or /job-postings"}

# Resume HTTP requests
@app.post("/resume", response_model=Resume)
async def add_resume(resume: Resume):
    with SessionLocal() as session:
        db_resume = ResumeDB(**resume.dict())
        session.add(db_resume)
        session.commit()
        session.refresh(db_resume)
        return db_resume

@app.delete("/resume", response_model=Resume)
async def del_resume(resume_id: int):
    with SessionLocal() as session:
        resume = session.query(ResumeDB).filter(ResumeDB.id == resume_id).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        session.delete(resume)
        session.commit()
        return resume

@app.get("/resumes", response_model=list[Resume])
async def get_resume():
    with SessionLocal() as session:
        resumes = session.query(ResumeDB).all()
        return resumes

# Generate a new resume using OpenAI
# TODO: Integrate it with database
@app.get("/create-resume")
async def create_resume():
    resume = generate_resume(os.getenv("open_ai_secret"))
    return {"New resume: ": resume}


# Suggestion requests
@app.post("/suggestion", response_model=Suggestion)
async def add_suggestion(suggestion: Suggestion):
    with SessionLocal() as session:
        db_suggestion = SuggestionDB(**suggestion.dict())
        session.add(db_suggestion)
        session.commit()
        session.refresh(db_suggestion)
        return db_suggestion

@app.delete("/suggestion", response_model=Suggestion)
async def del_suggestion(suggestion_id: int):
    with SessionLocal() as session:
        suggestion = session.query(SuggestionDB).filter(SuggestionDB.id == suggestion_id).first()
        if not suggestion:
            raise HTTPException(status_code=404, detail="Job Posting not found")
        session.delete(suggestion)
        session.commit()
        return suggestion

@app.get("/suggestions", response_model=list[Suggestion])
async def get_suggestions():
    with SessionLocal() as session:
        suggestions = session.query(SuggestionDB).all()
        return suggestions


# Job posting requests w/ JobPosting objects
@app.post("/job-posting", response_model=JobPosting)
async def add_job_posting(job_posting: JobPosting):
    with SessionLocal() as session:
        db_job_posting = JobPostingDB(**job_posting.dict())
        session.add(db_job_posting)
        session.commit()
        session.refresh(db_job_posting)
        return db_job_posting

@app.delete("/job-posting", response_model=JobPosting)
async def delete_job_posting(job_posting_id: int):
    with SessionLocal() as session:
        job_posting = session.query(JobPostingDB).filter(JobPostingDB.id == job_posting_id).first()
        if not job_posting:
            raise HTTPException(status_code=404, detail="Job Posting not found")
        session.delete(job_posting)
        session.commit()
        return job_posting

@app.get("/job-postings", response_model=list[JobPosting])
async def get_job_postings():
    with SessionLocal() as session:
        job_postings = session.query(JobPostingDB).all()
        return job_postings
    
@app.post("/optimize-resume")
async def optimize_resume(resume: Resume):
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
async def upload_resume(file: UploadFile = File(...)):
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
            
            # Create a new resume object
            resume = Resume(text=text)
            
            # Save to database
            with SessionLocal() as session:
                db_resume = ResumeDB(**resume.dict())
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