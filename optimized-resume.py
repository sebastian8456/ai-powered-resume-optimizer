from fastapi import FastAPI
app = FastAPI()

optimized_resume_list = []

@app.get("/")
async def root():
    return {"message": "Hello, please enter a valid endpoint: /optimized-resume"}

@app.post("/optimized-resume")
async def add_optimized_resume(original_resume_id: str = "", job_posting_id: str = "", match_score: float = 0.0):
    optimized_resume = {
        "original_resume_id": original_resume_id,
        "job_posting_id": job_posting_id,
        "match_score": match_score
    }
    optimized_resume_list.append(optimized_resume)
    return {"We have a new optimized resume with match score": match_score}

@app.delete("/optimized-resume")
async def del_optimized_resume():
    if len(optimized_resume_list > 0):
        optimized_resume_list.pop(-1)
    return {"Optimized Resume List": optimized_resume_list}

@app.get("/optimized-resume")
async def get_optimized_resumes():
    return {"Optimized Resume List": optimized_resume_list}