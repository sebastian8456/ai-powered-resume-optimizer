from fastapi import FastAPI, HTTPException
import openai
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["*"] for all origins (less secure)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key=""

job_postings_list = []

@app.get("/")
async def root():
    return {"message": "Hello, please enter a valid endpoint: /resume, /optimized-resume, or /job-posting"}

@app.post("/job-posting")
async def add_job_posting(job_posting: str = ""):
    job_postings_list.append(job_posting)
    return {"Added Job Posting": job_posting}

@app.delete("/job-posting")
async def del_string(job_posting: str = ""):
    if len(job_postings_list > 0):
        job_postings_list.pop(-1)
    return {"Job Posting List: ": job_postings_list}

@app.get("/job-posting")
async def get_string():
    return {"Job Posting List": job_postings_list}


@app.get("/job-suggestions")
async def get_job_suggestions(index: int = 0):
    if index < 0 or index >= len(job_postings_list):
        raise HTTPException(status_code=404, detail="Job posting not found")
    else:
        try:
            prompt = build_job_prompt(job_postings_list[index])
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return {"suggestions": response.choices[0].message.content}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

def build_job_prompt(job_posting):
    prompt = f"""Based on the job title "{job_posting}", suggest 10 similar job titles.
    Only list the 10 job titles."""
    return prompt