import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from core.config import settings
from db.database import engine, SessionLocal
from api.v1 import auth, platform
from datetime import datetime
from core.notifications import NotificationService

async def durable_worker():
    while True:
        try:
            with SessionLocal() as db:
                NotificationService.process_outbox(db)
        except Exception:
            pass
        await asyncio.sleep(5) 

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(durable_worker())
    yield
    task.cancel()

app = FastAPI(
    title=settings.PROJECT_NAME, 
    version=settings.VERSION, 
    lifespan=lifespan,
    debug=False,
    docs_url=None, 
    redoc_url=None 
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(platform.router, prefix=f"{settings.API_V1_STR}/platform", tags=["Platform"])

@app.get("/health", tags=["Observability"])
def health_check():
    return {"status": "operational", "version": settings.VERSION, "timestamp": datetime.utcnow().isoformat()}

@app.get("/app", response_class=HTMLResponse)
def serve_spa():
    with open("frontend/app.html", "r") as f:
        return f.read()
