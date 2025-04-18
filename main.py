from fastapi import FastAPI

app = FastAPI()

resume_list = []
optimized_resume_list = []
job_postings_list = []

@app.get("/")
async def root():
    return {"message": "Hello, please enter a valid endpoint: /resume, /optimized-resume, or /job-posting"}

# Original resume requests

@app.post("/resume")
async def add_resume(resume: str = ""):
    resume_list.append(resume)
    return {"We have a new resume: ": resume}

@app.delete("/resume")
async def del_resume(resume: str = ""):
    if len(resume_list) > 0:
        resume_list.pop(-1)
    return {"Resume List: ": resume_list}

@app.get("/resume")
async def get_resume():
    return {"Resume List: ": resume_list}


# Optimized resume requests
@app.post("/optimized-resume")
async def add_optimized_resume(optimized_resume: str = ""):
    optimized_resume_list.append(optimized_resume)
    return {"Optimized a resume: ": optimized_resume}

@app.delete("/optimized-resume")
async def del_optimized_resume(optimized_resume: str = ""):
    if len(optimized_resume_list) > 0:
        optimized_resume_list.pop(-1)
    return {"Optimized resumes: ": optimized_resume_list}

@app.get("/optimized-resume")
async def get_optimized_resume():
    return {"Optimized resumes: ": optimized_resume_list}

