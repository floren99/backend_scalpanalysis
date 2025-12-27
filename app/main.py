from fastapi import FastAPI
from app.routes import predict_routes, auth_routes
from app.database import Base, engine
from app import models

app = FastAPI(title="Scalp Analysis API")

@app.get("/")
def root():
    return {
        "status": "OK",
        "message": "Backend running",
        "docs": "/docs"
    }
Base.metadata.create_all(bind=engine)

app.include_router(auth_routes.router)
app.include_router(predict_routes.router)
app.include_router(predict_routes.router)
