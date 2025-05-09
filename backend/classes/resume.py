from pydantic import BaseModel
from typing import Optional

class Resume(BaseModel):
    id: Optional[int] = None
    text: str

    class Config():
        orm_mode = True