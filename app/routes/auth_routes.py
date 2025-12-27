from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from app.database import get_db
from app.models import User
from app.auth import hash_password, verify_password, create_token
import re

router = APIRouter(prefix="/auth", tags=["Auth"])


# ======================
# SCHEMAS (INLINE)
# ======================
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3)
    full_name: str
    gender: str
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    username: str
    password: str


# ======================
# UTIL VALIDATION
# ======================
def validate_password(password: str):
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="Password harus mengandung huruf besar")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=400, detail="Password harus mengandung huruf kecil")
    if not re.search(r"[0-9]", password):
        raise HTTPException(status_code=400, detail="Password harus mengandung angka")
    if not re.search(r"[.@!#]", password):
        raise HTTPException(
            status_code=400,
            detail="Password harus mengandung karakter khusus (. @ ! #)"
        )


# ======================
# REGISTER
# ======================
@router.post("/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username sudah digunakan")

    validate_password(data.password)

    user = User(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        gender=data.gender,
        hashed_password=hash_password(data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Register berhasil",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "gender": user.gender
        }
    }


# ======================
# LOGIN
# ======================
@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Username atau password salah")

    token = create_token({
        "user_id": user.id,
        "username": user.username
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }
