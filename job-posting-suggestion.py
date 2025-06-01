from fastapi import FastAPI, HTTPException
import openai
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import re
from keybert import KeyBERT

app = FastAPI()

kw_model = KeyBERT(model='all-MiniLM-L6-v2')

openai.api_key = ""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DATABASE SETUP ----------
DATABASE_URL = " "
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------- SQLAlchemy Model ----------
class JobPosting(Base):
    __tablename__ = "job_postings"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    requirements = Column(Text)

Base.metadata.create_all(bind=engine)

# ---------- MODELS ----------
class ResumeText(BaseModel):
    text: str

# ---------- UTILITIES ----------
def extract_keywords_semantic(text: str, top_n: int = 10) -> list:
    truncated_text = text[:10000]
    keywords = kw_model.extract_keywords(
        truncated_text,
        keyphrase_ngram_range=(1, 2),
        stop_words='english',
        top_n=top_n
    )
    return [kw for kw, _ in keywords]

def normalize_title(title: str) -> str:
    normalized_title = title.lower()
    normalized_title = re.sub(r'\b(position|now open|available|job)\b', '', normalized_title)
    return " ".join(normalized_title.split())

def extract_section(text: str, section_name: str) -> str:
    pattern = rf"{section_name}:\s*(.*?)(?=\n[A-Z][a-z]+:|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else "Not found"

def extract_keywords(text: str) -> set:
    """Extract a set of simple keywords from a text block"""
    words = re.findall(r'\b\w+\b', text.lower())
    return set(words)

# ENDPOINTS FOR GENERATE JOB POSTING
@app.get("/")
async def root():
    return {"message": "Try /generate-job-posting or /job-postings"}

@app.post("/generate-job-posting")
async def generate_job_posting_from_text(data: ResumeText):
    resume_text = data.text
    semantic_keywords = extract_keywords_semantic(resume_text)
    top_keywords = ', '.join(semantic_keywords)

    prompt = f"""
    Based on the following professional keywords extracted from a resume, generate a relevant job posting.
    Keywords: {top_keywords}

    Format the output as:
    Title: ...
    Description: ...
    Responsibilities:
    - ...
    Requirements:
    - ...
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        title = extract_section(content, "Title")
        description = extract_section(content, "Description")
        requirements = extract_section(content, "Requirements")

        db = SessionLocal()
        job_post = JobPosting(title=title, description=description, requirements=requirements)
        db.add(job_post)
        db.commit()
        db.refresh(job_post)

        return {
            "message": "Job posting successfully generated from resume",
            "id": job_post.id,
            "title": title,
            "description": description,
            "requirements": requirements
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# ENDPOINTS FOR MATCH JOBS BASE ON THE RESUME
@app.post("/match-resume")
async def match_resume(data: ResumeText):
    resume_text = data.text
    resume_keywords = extract_keywords(resume_text)

    db: Session = SessionLocal()
    try:
        job_posts = db.query(JobPosting).all()
        matched_jobs = []
        matched_job_titles = set()

        for job in job_posts:
            combined_text = f"{job.description}\n{job.requirements}"
            posting_keywords = extract_keywords(combined_text)
            matched = resume_keywords & posting_keywords
            score = len(matched)

            normalized_title = normalize_title(job.title)

            if score > 0 and normalized_title not in matched_job_titles:
                matched_job_titles.add(normalized_title)
                matched_jobs.append({
                    "job_id": job.id,
                    "job_title": job.title,
                    "job_description": job.description,
                    "job_requirements": job.requirements
                })

        return {"matches": matched_jobs}
    finally:
        db.close()
