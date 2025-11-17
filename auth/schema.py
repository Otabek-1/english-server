from pydantic import BaseModel

class RegisterUser(BaseModel):
    username:str
    email:str
    password:str

class LoginUser(BaseModel):
    email:str
    password:str

class TokenRefreshSchema(BaseModel):
    refresh_token: str