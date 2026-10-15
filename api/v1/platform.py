import subprocess
from fastapi import BackgroundTasks
from pydantic import BaseModel
import hashlib, json, io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from db.models import UserProfile, Opportunity, Application, VerificationAudit
from api.deps import get_current_user
from core.eligibility import DeterministicEligibilityEngine
from core.ai_service import AIService
from datetime import datetime
import PyPDF2

router = APIRouter()

class StatusUpdateSchema(BaseModel): new_status: str
class ProfileUpdateSchema(BaseModel): updates: dict

@router.get("/home")
def get_home(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    opps = db.query(Opportunity).all()
    hero_opp = next((o for o in opps if "Cyber" in (o.tags or [])), opps[0] if opps else None)
    
    return {
        "profile": {
            "name": profile.full_name, 
            "institution": profile.institution, 
            "degree": profile.degree, 
            "age": profile.age, 
            "graduation_year": profile.graduation_year
        } if profile else None,
        "hero": {
            "id": hero_opp.id, 
            "title": hero_opp.title, 
            "org": hero_opp.organization, 
            "date": hero_opp.closing_date.strftime("%Y-%m-%d") if hero_opp.closing_date else "No Deadline"
        } if hero_opp else None,
        "carousels": [{
            "id": "top", 
            "title": "Priority Targets", 
            "items": [{
                "id": o.id, 
                "title": o.title, 
                "org": o.organization, 
                "date": o.closing_date.strftime("%Y-%m-%d") if o.closing_date else "No Deadline"
            } for o in opps]
        }]
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
    ai_explanation = AIService.explain_eligibility(status, steps)
    
    existing_audit = db.query(VerificationAudit).filter(VerificationAudit.user_id == current_user.id, VerificationAudit.opportunity_id == opp.id).order_by(VerificationAudit.evaluated_at.desc()).first()
    if not existing_audit or existing_audit.status != status:
        audit = VerificationAudit(user_id=current_user.id, opportunity_id=opp.id, status=status, evidence_chain=steps, evaluated_at=datetime.utcnow())
        db.add(audit)
        db.commit()
    
    return {"status": status, "steps": steps, "ai_explanation": ai_explanation}

@router.post("/profile/resume/upload")
async def upload_resume(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    content = await file.read()
    try:
        pdf = PyPDF2.PdfReader(io.BytesIO(content))
        text = "".join([page.extract_text() for page in pdf.pages])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid PDF file.")
    
    proposed_updates = AIService.extract_profile_from_resume(text)
    return {"status": "success", "proposed_updates": proposed_updates}

@router.post("/profile/resume/confirm")
def confirm_profile_updates(data: ProfileUpdateSchema, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    for key, value in data.updates.items():
        if hasattr(profile, key):
            setattr(profile, key, value)
    db.commit()
    return {"status": "success", "message": "Profile updated securely."}
class ScraperStatus(BaseModel):
    message: str
    status: str

@router.post("/scrape", response_model=ScraperStatus)
def trigger_scraper(background_tasks: BackgroundTasks):
    def run_scraper_script():
        try:
            subprocess.run(["python", "scripts/scrape_dynamic.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Scraping failed: {e}")

    background_tasks.add_task(run_scraper_script)
    return {"message": "Dynamic web scraper initiated.", "status": "running"}