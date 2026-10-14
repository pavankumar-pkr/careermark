import os

FILES = {}

FILES["core/eligibility.py"] = '''import json

class DeterministicEligibilityEngine:
    @staticmethod
    def evaluate(profile, requirements):
        steps = []
        final_status = "eligible"
        
        for req in requirements:
            profile_val = getattr(profile, req.field_name, None)
            status = "unknown"
            
            if profile_val is None or str(profile_val).strip() == "":
                if final_status != "not_eligible": final_status = "cannot_verify"
                status = "cannot_verify"
            else:
                passed = False
                try:
                    if req.operator == '==': passed = str(profile_val).lower() == str(req.target_value).lower()
                    elif req.operator == '<=': passed = float(profile_val) <= float(req.target_value)
                    elif req.operator == '>=': passed = float(profile_val) >= float(req.target_value)
                    elif req.operator == 'IN': passed = str(profile_val) in json.loads(req.target_value)
                except ValueError:
                    if final_status != "not_eligible": final_status = "cannot_verify"
                    status = "cannot_verify"
                else:
                    status = "pass" if passed else "fail"
                    if not passed: final_status = "not_eligible"
            
            steps.append({
                "field": req.field_name.replace("_", " ").title(),
                "requirement_text": req.requirement_text,
                "rule": f"{req.field_name} {req.operator} {req.target_value}",
                "profile_val": profile_val if profile_val else "Not provided",
                "status": status
            })
            
        return final_status, steps
'''

FILES["main.py"] = '''import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from core.config import settings
from db.database import engine, SessionLocal
from api.v1 import auth, platform
from datetime import datetime

async def deadline_monitor():
    while True:
        try:
            with SessionLocal() as db:
                now = datetime.utcnow()
        except Exception as e:
            pass
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(deadline_monitor())
    yield
    task.cancel()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

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
'''

FILES["api/v1/platform.py"] = '''import hashlib, json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from db.models import UserProfile, Opportunity, Application, VerificationAudit
from api.deps import get_current_user
from core.eligibility import DeterministicEligibilityEngine
from datetime import datetime

router = APIRouter()
class StatusUpdateSchema(BaseModel): new_status: str

@router.get("/home")
def get_home(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    opps = db.query(Opportunity).all()
    hero_opp = next((o for o in opps if "Cyber" in (o.tags or [])), opps[0] if opps else None)
    return {
        "profile": {"name": profile.full_name, "institution": profile.institution, "degree": profile.degree},
        "hero": {"id": hero_opp.id, "title": hero_opp.title, "org": hero_opp.organization, "date": hero_opp.closing_date.strftime("%Y-%m-%d")} if hero_opp else None,
        "carousels": [{"id": "top", "title": "Priority Targets", "items": [{"id": o.id, "title": o.title, "org": o.organization, "date": o.closing_date.strftime("%Y-%m-%d")} for o in opps]}]
    }

@router.get("/pipeline")
def get_pipeline(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    apps = db.query(Application).filter(Application.user_id == current_user.id).all()
    pipeline = {"Target Identified": [], "Preparation Active": [], "Application Submitted": []}
    for app in apps:
        if app.status in pipeline:
            pipeline[app.status].append({"app_id": app.id, "title": app.opportunity.title, "org": app.opportunity.organization, "date": app.opportunity.closing_date.strftime("%Y-%m-%d")})
    return pipeline

@router.put("/pipeline/{app_id}")
def update_pipeline(app_id: int, data: StatusUpdateSchema, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
    if not app: raise HTTPException(status_code=404, detail="Application not found")
    app.status = data.new_status
    db.commit()
    return {"status": "success"}

@router.get("/evaluate/{opp_id}")
def evaluate_opportunity(opp_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp: raise HTTPException(status_code=404, detail="Opportunity not found")
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    status, steps = DeterministicEligibilityEngine.evaluate(profile, opp.requirements)
    
    existing_audit = db.query(VerificationAudit).filter(VerificationAudit.user_id == current_user.id, VerificationAudit.opportunity_id == opp.id).order_by(VerificationAudit.evaluated_at.desc()).first()
    if not existing_audit or existing_audit.status != status:
        audit = VerificationAudit(user_id=current_user.id, opportunity_id=opp.id, status=status, evidence_chain=steps, evaluated_at=datetime.utcnow())
        db.add(audit)
        db.commit()
    
    return {"status": status, "steps": steps}
'''

for path, content in FILES.items():
    with open(path, "w") as f:
        f.write(content)

html_path = "frontend/app.html"
with open(html_path, "r") as f:
    html = f.read()

html = html.replace("const token = ref('');", "const token = ref(localStorage.getItem('cm_token') || '');\n                if (token.value) { currentView.value = 'home'; loadAllData(); }")
html = html.replace("token.value = data.token;", "token.value = data.token; localStorage.setItem('cm_token', data.token);")
html = html.replace("token.value = '';", "token.value = ''; localStorage.removeItem('cm_token');")

with open(html_path, "w") as f:
    f.write(html)
