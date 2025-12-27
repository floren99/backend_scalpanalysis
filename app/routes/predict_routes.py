from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.ml.hair_classification import predict
from app.database import get_db
from app import models

router = APIRouter(prefix="/predict", tags=["Predict"])

@router.post("/")
async def analyze(
    file: UploadFile = File(...),
    gender: str = "male",
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

    return {
        "disease": label,
        "confidence": round(confidence * 100, 2),
        "healthy_reference": f"/static/healthy/{gender}.jpg"
    }
