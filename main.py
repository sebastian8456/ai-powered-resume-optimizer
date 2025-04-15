from fastapi import FastAPI

app = FastAPI()

resume_list = []

@app.get("/")
async def root():
    return {"message": "Hello, please enter a valid endpoint: /resume"}

@app.post("/resume")
async def add_string(resume: str = ""):
    resume_list.append(resume)
    return {"We have a new resume"}

@app.delete("/resume")
async def del_string(resume: str = ""):
    if len(resume_list > 0):
        resume_list.pop(-1)
    return {"Resume List: ": resume_list}


@app.get("/resume")
async def get_string():
    return {"Resume List: ": resume_list}