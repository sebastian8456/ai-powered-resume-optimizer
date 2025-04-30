from fastapi import FastAPI
from pydantic import BaseModel

# ---------- Pydantic Models ----------
class Resume(BaseModel):
    content: str

class OptimizedResume(BaseModel):
    content: str

class JobPosting(BaseModel):
    description: str

class Restaurant(BaseModel):
    id: int
    name: str
    address: str

    class Config:
        orm_mode = True

# Sample restaurant data
restaurant_list = [
    Restaurant(id=1, name="Chipotle", address="123 Main St"),
    Restaurant(id=2, name="Olive Garden", address="456 Maple Ave"),
    Restaurant(id=3, name="Sushi Place", address="789 Oak Blvd")
]

# ---------- FastAPI App ----------
app = FastAPI()

resume_list = []
optimized_resume_list = []
job_postings_list = []

@app.get("/")
async def root():
    return {"message": "Hello, please enter a valid endpoint: /resume, /optimized-resume, or /job-posting"}

# Resume endpoints
@app.post("/resume")
async def add_resume(resume: Resume):
    resume_list.append(resume.content)
    return {"We have a new resume": resume.content}

@app.delete("/resume")
async def del_resume():
    if resume_list:
        resume_list.pop(-1)
    return {"Resume List": resume_list}

@app.get("/resume")
async def get_resume():
    return {"Resume List": resume_list}

# Optimized resume endpoints
@app.post("/optimized-resume")
async def add_optimized_resume(optimized_resume: OptimizedResume):
    optimized_resume_list.append(optimized_resume.content)
    return {"Optimized a resume": optimized_resume.content}

@app.delete("/optimized-resume")
async def del_optimized_resume():
    if optimized_resume_list:
        optimized_resume_list.pop(-1)
    return {"Optimized resumes": optimized_resume_list}

@app.get("/optimized-resume")
async def get_optimized_resume():
    return {"Optimized resumes": optimized_resume_list}

# Job posting endpoints
@app.post("/job-posting")
async def add_job_posting(job_posting: JobPosting):
    job_postings_list.append(job_posting.description)
    return {"A new job posting just added": job_posting.description}

@app.delete("/job-posting")
async def del_job_posting():
    if job_postings_list:
        job_postings_list.pop(-1)
    return {"Job Posting List": job_postings_list}

@app.get("/job-posting")
async def get_job_posting():
    return {"Job Posting List": job_postings_list}
