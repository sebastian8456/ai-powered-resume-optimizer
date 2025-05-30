from pydantic import BaseModel

class Suggestion(BaseModel):
    id: int
    suggestion: str

    model_config = {
        "from_attributes": True
    }