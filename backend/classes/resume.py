from pydantic import BaseModel
from typing import Optional

class Resume(BaseModel):
    id: Optional[int] = None
    text: str

    model_config = {
        "from_attributes": True
    }