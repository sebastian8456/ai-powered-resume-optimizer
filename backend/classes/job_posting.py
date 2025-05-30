from pydantic import BaseModel

class JobPosting(BaseModel):
    id: int
    title: str
    company: str

    model_config = {
        "from_attributes": True
    }
        