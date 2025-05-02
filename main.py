from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import requests
from backend.APIs.open_ai import *
from backend.classes.resume import *
from backend.classes.job_posting import *
from backend.classes.suggestion import *
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

app = FastAPI()
load_dotenv()

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