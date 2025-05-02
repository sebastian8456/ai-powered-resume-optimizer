from pydantic import BaseModel

class JobPosting(BaseModel):
    id: int
    title: str
    company: str

    class Config():
        orm_mode = True
