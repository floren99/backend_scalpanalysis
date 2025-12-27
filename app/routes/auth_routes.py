from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import hash_password, verify_password, create_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def register(
    email: str,
    username: str,
    full_name: str,
    gender: str,
    password: str,
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    user = User(
        email=email,
        username=username,
        full_name=full_name,
        gender=gender,
        hashed_password=hash_password(password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Register berhasil"}


@router.post("/login")
def login(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Username / password salah")

    token = create_token({
        "user_id": user.id,
        "username": user.username
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }
