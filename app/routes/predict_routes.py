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

@router.post("/")
async def analyze(
    file: UploadFile = File(...),
    gender: Literal["male", "female"] = Query("male"),
    user_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    # 1️⃣ Validasi tipe file
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File harus berupa gambar (jpg/png)"
        )

    try:
        # 2️⃣ Read image bytes
        img_bytes = await file.read()

        # 3️⃣ Predict
        label, confidence = predict(img_bytes)

        # 4️⃣ Simpan file ke static/uploads
        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(img_bytes)

        image_url = f"/static/uploads/{filename}"

        # 5️⃣ Simpan ke DB (kalau login)
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

        disease_info = get_disease_info(label)

        return {
            "disease": label,
            "display_name": disease_info["display_name"],
            "confidence": round(confidence * 100, 2),
            "user_image": image_url,            # ⬅️ image user
            "healthy_reference": healthy_map.get(gender),
            "recommendations": disease_info["recommendation"]
        }

    except ValueError as e:
        return {
            "error": "Gambar yang diunggah kurang tepat",
            "message": str(e),
            "tips": [
                "Pastikan gambar fokus pada kulit kepala",
                "Hindari gambar buram atau gelap",
                "Jangan terhalang rambut atau aksesori"
            ]
        }
