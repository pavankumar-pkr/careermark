from fastapi import FastAPI
from core.config import settings
from api.v1 import auth, platform

app = FastAPI(
    title="CareerMark API",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(platform.router, prefix=settings.API_V1_STR)

@app.get("/")
def home():
    return {"status": "CareerMark Backend is Live!", "documentation": "/docs"}
