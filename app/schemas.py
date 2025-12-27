from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    gender: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str
