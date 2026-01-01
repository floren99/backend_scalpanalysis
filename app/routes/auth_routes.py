from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User, PasswordReset
from app.auth import hash_password, verify_password, create_token, generate_reset_code
from app.utils.email import send_reset_email
import re

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3)
    full_name: str
    gender: str
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str = Field(..., min_length=8)


def validate_password(password: str):
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="Password harus mengandung huruf besar")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=400, detail="Password harus mengandung huruf kecil")
    if not re.search(r"[0-9]", password):
        raise HTTPException(status_code=400, detail="Password harus mengandung angka")
    if not re.search(r"[.@!#]", password):
        raise HTTPException(status_code=400, detail="Password harus mengandung karakter khusus")


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
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

    return {"message": "Register berhasil"}


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Username atau password salah")

    token = create_token({"user_id": user.id, "username": user.username})

    return {"access_token": token, "token_type": "bearer"}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Email tidak terdaftar")

    db.query(PasswordReset).filter(
        PasswordReset.user_id == user.id
    ).delete()

    code = generate_reset_code()
    expired = datetime.utcnow() + timedelta(minutes=10)

    reset = PasswordReset(
        user_id=user.id,
        code=code,
        expired_at=expired
    )

    db.add(reset)
    db.commit()

    try:
        send_reset_email(user.email, code)
    except Exception:
        pass

    return {"message": "Kode reset dikirim"}


@router.post("/verify-reset-code")
def verify_reset_code(data: VerifyResetCodeRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email tidak terdaftar")

    reset = db.query(PasswordReset).filter(
        PasswordReset.user_id == user.id,
        PasswordReset.code == data.code,
        PasswordReset.expired_at > datetime.utcnow()
    ).first()

    if not reset:
        raise HTTPException(status_code=400, detail="Kode tidak valid atau kadaluarsa")

    return {"message": "Kode valid"}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    validate_password(data.new_password)

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    reset = db.query(PasswordReset).filter(
        PasswordReset.user_id == user.id,
        PasswordReset.code == data.code,
        PasswordReset.expired_at > datetime.utcnow()
    ).first()

    if not reset:
        raise HTTPException(status_code=400, detail="Kode tidak valid atau kadaluarsa")

    user.hashed_password = hash_password(data.new_password)
    db.delete(reset)
    db.commit()

    return {"message": "Password berhasil diubah"}
