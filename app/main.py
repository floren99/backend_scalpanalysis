from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import predict_routes, auth_routes
from app.database import Base, engine
from app import models
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="Scalp Analysis API",
    description="API untuk analisis kondisi kulit kepala berbasis GANs dan CNN VGG16",
    version="1.0.0"
)


Base.metadata.create_all(bind=engine)


if not os.path.exists("static"):
    os.makedirs("static/uploads", exist_ok=True)
    os.makedirs("static/healthy", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(auth_routes.router)
app.include_router(predict_routes.router)


@app.get("/")
def root():
    return {
        "status": "OK",
        "message": "Backend running",
        "docs": "/docs"
    }
