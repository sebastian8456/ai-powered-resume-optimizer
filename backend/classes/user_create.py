from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    name: str
    password: str