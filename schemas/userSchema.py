from pydantic import BaseModel

class promoteData(BaseModel):
    id: int

class udpateUser(BaseModel):
    username:str
    email:str

class passwordChange(BaseModel):
    old_password:str
    new_password:str

class premium(BaseModel):
    id:int