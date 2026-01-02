from fastapi import APIRouter, UploadFile, File, Depends, Query
from sqlalchemy.orm import Session
from typing import Literal

from app.ml.hair_classification import predict, get_disease_info
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

        # Simpan history jika ada user_id
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

        # Ambil info penyakit & rekomendasi
        disease_info = get_disease_info(label)

        return {
            "disease": label,
            "confidence": round(confidence * 100, 2),
            "healthy_reference": healthy_map.get(gender, ""),
            "display_name": disease_info["display_name"],
            "recommendations": disease_info["recommendation"]
        }

    except ValueError as e:
        # Pesan friendly jika gambar kurang valid / bukan kulit kepala
        return {
            "error": "Gambar yang diunggah kurang tepat.",
            "message": str(e),
            "tips": [
                "Pastikan gambar adalah kulit kepala yang jelas.",
                "Hindari gambar yang buram, terlalu gelap, atau terhalang rambut/aksesori.",
                "Ambil gambar dari jarak dekat dan fokus ke area kulit kepala."
            ]
        }
