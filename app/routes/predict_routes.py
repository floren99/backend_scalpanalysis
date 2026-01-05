from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Literal
import uuid
import os

from app.ml.hair_classification import predict, get_disease_info
from app.database import get_db
from app import models

router = APIRouter(prefix="/predict", tags=["Predict"])


UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "heic", "heif"}

@router.post("/")
async def analyze(
    file: UploadFile = File(...),
    gender: Literal["male", "female"] = Query("male"),
    user_id: int | None = Query(None),
    db: Session = Depends(get_db),
):

    if not file.filename:
        raise HTTPException(status_code=400, detail="File tidak valid")

    ext = file.filename.lower().split(".")[-1]
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Format gambar tidak didukung (jpg, jpeg, png, heic)"
        )

    try:
 
        img_bytes = await file.read()
        if not img_bytes:
            raise ValueError("File gambar kosong")


        label, confidence = predict(img_bytes)


        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(img_bytes)

        image_url = f"/static/uploads/{filename}"


        if user_id:
            history = models.History(
                user_id=user_id,
                disease=label,
                confidence=confidence,
                image_path=image_url
            )
            db.add(history)
            db.commit()


        healthy_map = {
            "male": "/static/healthy/male.png",
            "female": "/static/healthy/female.jpg"
        }


        disease_info = get_disease_info(label) or {
            "display_name": label,
            "recommendation": []
        }

        # RESPONSE
        return {
            "disease": label,
            "display_name": disease_info["display_name"],
            "confidence": round(confidence * 100, 2),
            "user_image": image_url,
            "healthy_reference": healthy_map.get(gender),
            "recommendations": disease_info["recommendation"]
        }

    except ValueError as e:
        return {
            "error": "Gambar yang diunggah kurang tepat",
            "message": str(e),
            "tips": [
                "Pastikan gambar fokus pada kulit kepala",
                "Hindari gambar buram atau terlalu gelap",
                "Pastikan tidak terhalang rambut atau aksesori"
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan server: {str(e)}"
        )
