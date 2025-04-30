from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Set up OpenAI client with API key from .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Dummy in-memory storage for optimized resumes
optimized_resume_list = []

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Hello, please enter a valid endpoint: /optimized-resume"}

# POST to add an optimized resume
@app.post("/optimized-resume")
async def add_optimized_resume(original_resume_id: str = "", job_posting_id: str = "", match_score: float = 0.0):
    optimized_resume = {
        "original_resume_id": original_resume_id,
        "job_posting_id": job_posting_id,
        "match_score": match_score
    }
    optimized_resume_list.append(optimized_resume)
    return {"We have a new optimized resume with match score": match_score}

# DELETE the most recent optimized resume
@app.delete("/optimized-resume")
async def del_optimized_resume():
    if len(optimized_resume_list) > 0:
        optimized_resume_list.pop(-1)
    return {"Optimized Resume List": optimized_resume_list}

# GET all optimized resumes
@app.get("/optimized-resume")
async def get_optimized_resumes():
    return {"Optimized Resume List": optimized_resume_list}

# Define expected input structure
class ResumeData(BaseModel):
    resume: str
    job_description: str

# POST to generate suggestions using OpenAI
@app.post("/optimize-resume")
async def optimize_resume(data: ResumeData):
    prompt = f"""
    Analyze the following resume and job description.
    Give helpful suggestions to improve the resume for this job.

    Resume:
    {data.resume}

    Job Description:
    {data.job_description}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful resume optimization assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        suggestions = response.choices[0].message.content.strip()
        return {"suggestions": suggestions}

    except Exception as e:
        error_message = str(e)
        if "insufficient_quota" in error_message or "quota" in error_message:
            return {"error": "OpenAI quota exceeded or not configured. No request was billed. Check your API billing settings."}
        return {"error": error_message}
