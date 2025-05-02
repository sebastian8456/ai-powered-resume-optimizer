from pydantic import BaseModel

class Suggestion(BaseModel):
    id: int
    suggestion: str

    class Config():
        orm_mode = True