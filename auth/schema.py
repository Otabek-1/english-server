from pydantic import BaseModel, EmailStr, Field


class RegisterUser(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenRefreshSchema(BaseModel):
    refresh_token: str = Field(..., min_length=1)