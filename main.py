from fastapi import FastAPI
from core.config import settings
from api.v1 import auth, platform
from db.database import engine, Base

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CareerMark API",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(platform.router, prefix=settings.API_V1_STR)

@app.get("/")
def home():
    return {"status": "CareerMark Backend is Live!", "documentation": "/docs"}
