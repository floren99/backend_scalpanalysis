from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Literal

from app.ml.hair_classification import predict
from app.database import get_db
from app import models

router = APIRouter(prefix="/predict", tags=["Predict"])

@router.post("/")
async def analyze(
    file: UploadFile = File(...),
    gender: Literal["male", "female"] = Query("male"),
    db: Session = Depends(get_db),
    user_id: int | None = None
):
    try:
        img_bytes = await file.read()
        label, confidence = predict(img_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if user_id:
        history = models.History(
            user_id=user_id,
            disease=label,
            confidence=confidence
        )
        db.add(history)
        db.commit()

    # mapping file healthy reference
    healthy_map = {
        "male": "/static/healthy/male.png",
        "female": "/static/healthy/female.jpg"
    }

    return {
        "disease": label,
        "confidence": round(confidence * 100, 2),
        "healthy_reference": healthy_map[gender]
    }
