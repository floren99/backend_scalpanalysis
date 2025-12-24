from fastapi import FastAPI
from app.routes import predict_routes

app = FastAPI(title="Scalp Analysis API")

@app.get("/")
def root():
    return {
        "status": "OK",
        "message": "Backend running",
        "docs": "/docs"
    }

app.include_router(predict_routes.router)
