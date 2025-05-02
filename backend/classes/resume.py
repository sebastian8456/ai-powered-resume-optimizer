from pydantic import BaseModel

class Resume(BaseModel):
    id: int
    text: str

    class Config():
        orm_mode = True