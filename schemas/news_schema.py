from pydantic import BaseModel

class News(BaseModel):
    title: str
    body: str

class React(BaseModel):
    emoji:str