from fastapi import FastAPI, HTTPException
import openai
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import re
from keybert import KeyBERT

app = FastAPI()

kw_model = KeyBERT(model='all-MiniLM-L6-v2')

openai.api_key = " "

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

def extract_section(text: str, section_name: str) -> str:
    pattern = rf"^{section_name}:\s*(.*?)(?=^\w.+?:|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else "Not provided"


# ENDPOINT FOR MATCH JOB POSTING
@app.get("/")
async def root():
    return {"message": "Try /match-me-job-posting"}

@app.post("/match-me-job-posting")
async def match_me_job_posting(data: ResumeText):
    resume_text = data.text
    semantic_keywords = sorted(extract_keywords_semantic(resume_text))
    top_keywords = ', '.join(semantic_keywords)

    prompt = f"""
    Based on the following professional keywords extracted from a resume, generate a detailed job posting. 

    Make sure the output includes the following sections with exact headers starting at the beginning of a line:

    Job Title: [Job Title here]

    Position Summary: [Brief summary of the position]

    Overview: [Overview of the company and role]

    Responsibilities:
    - [Responsibility 1]
    - [Responsibility 2]
    - ...

    Qualifications:
    - [Qualification 1]
    - [Qualification 2]
    - ...

    Key Skills:
    - [Key skill 1]
    - [Key skill 2]
    - ...

    Education: [Required education]

    Salary Range: [Salary range if applicable]

    Benefits:
    - [Benefit 1]
    - [Benefit 2]
    - ...

    Keywords: {top_keywords}
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            top_p=1
        )
        content = response.choices[0].message.content.strip()

        # Helper to extract sections with fallback
        def get_section(name):
            return extract_section(content, name) or "Not provided"

        return {
        "job_title": get_section("Job Title"),
        "position_summary": get_section("Position Summary"),
        "overview": get_section("Overview"),
        "responsibilities": get_section("Responsibilities"),
        "qualifications": get_section("Qualifications"),
        "key_skills": get_section("Key Skills"),
        "education": get_section("Education"),
        "salary_range": get_section("Salary Range"),
        "benefits": get_section("Benefits"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")