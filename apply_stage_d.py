import os

FILES = {}

# =====================================================================
# 1. AI SERVICE LAYER (Simulated for Local Safety)
# =====================================================================
FILES["core/ai_service.py"] = '''class AIService:
    @staticmethod
    def explain_eligibility(status: str, steps: list) -> str:
        """Translates deterministic engine output into human-readable explanations."""
        if status == "eligible":
            return "Good news! Based on the provided evidence in your profile, you meet all the official requirements for this opportunity."
        elif status == "cannot_verify":
            missing = [s['field'] for s in steps if s['status'] == 'cannot_verify']
            fields = ", ".join(missing) if missing else "some required fields"
            return f"We cannot definitively verify your eligibility yet. Please update your profile with your {fields} to get a final determination."
        else:
            failed = [s['field'] for s in steps if s['status'] == 'fail']
            fields = ", ".join(failed) if failed else "certain requirements"
            return f"Based on official rules, you do not meet the criteria for this role, specifically regarding your {fields}."

    @staticmethod
    def extract_profile_from_resume(text: str) -> dict:
        """Simulates an LLM extracting structured fields from raw PDF text."""
        # In a real environment, this passes `text` to OpenAI/Gemini with a JSON schema.
        # For local safety, we return a mocked extraction to test the UI confirmation flow.
        return {
            "degree": "B.Tech",
            "branch": "Computer Science",
            "graduation_year": 2026,
            "age": 22
        }
'''

# =====================================================================
# 2. UPDATE PLATFORM ROUTER (Add Resume Parsing & AI Explanations)
# =====================================================================
FILES["api/v1/platform.py"] = '''import hashlib, json, io
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
        "profile": {"name": profile.full_name, "institution": profile.institution, "degree": profile.degree, "age": profile.age, "graduation_year": profile.graduation_year},
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
'''

# =====================================================================
# 3. PATCH FRONTEND (Add AI Explanation & Resume Upload Flow)
# =====================================================================
html_path = "frontend/app.html"
with open(html_path, "r") as f:
    html = f.read()

# 3A: Add AI Explanation Box to Trust Engine
engine_ui_target = '<div class="p-8 flex-1">'
ai_box_html = '''<div class="p-8 flex-1">
                            <!-- AI EXPLANATION LAYER -->
                            <transition name="reveal">
                                <div v-if="evaluationState !== 'running' && aiExplanation" class="mb-6 p-4 rounded-lg bg-cm-blue/10 border border-cm-blue/20 flex items-start">
                                    <i class="fas fa-sparkles text-cm-blue mt-1 mr-3"></i>
                                    <div>
                                        <h4 class="text-xs font-bold text-cm-blue uppercase tracking-wider mb-1">AI Analysis</h4>
                                        <p class="text-sm text-cm-text leading-relaxed">{{ aiExplanation }}</p>
                                    </div>
                                </div>
                            </transition>
'''
html = html.replace(engine_ui_target, ai_box_html)

# 3B: Replace Locked Profile UI with AI Resume Upload UI
profile_ui_old = '<div class="surface-card p-8 text-center"><i class="fas fa-lock text-cm-muted text-2xl mb-3"></i><p class="text-sm text-cm-muted">Full profile editing is locked in the Phase 14 Trust Engine preview.</p></div>'
profile_ui_new = '''
                        <div class="surface-card p-6 mb-6">
                            <h3 class="font-bold text-white mb-4">Current Verified Data</h3>
                            <div class="grid grid-cols-2 gap-4 text-sm">
                                <div><span class="block text-xs text-cm-muted">Degree</span><span class="text-white">{{ homeData.profile?.degree || 'Not Provided' }}</span></div>
                                <div><span class="block text-xs text-cm-muted">Graduation Year</span><span class="text-white">{{ homeData.profile?.graduation_year || 'Not Provided' }}</span></div>
                                <div><span class="block text-xs text-cm-muted">Age</span><span class="text-white">{{ homeData.profile?.age || 'Not Provided' }}</span></div>
                            </div>
                        </div>

                        <div class="surface-card p-6">
                            <h3 class="font-bold text-white mb-2"><i class="fas fa-file-pdf text-red-400 mr-2"></i> AI Resume Extraction</h3>
                            <p class="text-xs text-cm-muted mb-4">Upload your PDF resume. Our local AI will extract your credentials for your review. No data is saved without your explicit confirmation.</p>
                            
                            <input type="file" @change="handleFileUpload" accept=".pdf" class="block w-full text-sm text-cm-muted file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-cm-blue file:text-white hover:file:bg-blue-600 cursor-pointer mb-4">
                            
                            <div v-if="isParsingResume" class="text-cm-blue text-xs mt-2"><i class="fas fa-circle-notch fa-spin mr-2"></i> Analyzing document...</div>
                            
                            <div v-if="proposedProfile" class="mt-4 p-4 border border-cm-verified/30 bg-cm-verified/10 rounded-lg">
                                <h4 class="text-xs font-bold text-cm-verified uppercase tracking-wider mb-3">Proposed Updates Found</h4>
                                <ul class="space-y-2 text-sm text-white mb-4">
                                    <li v-for="(val, key) in proposedProfile" :key="key"><span class="text-cm-muted uppercase text-[10px] w-24 inline-block">{{ key }}</span> {{ val }}</li>
                                </ul>
                                <button @click="confirmProfileUpdates" class="bg-cm-verified text-cm-bg px-4 py-2 rounded font-medium hover:bg-teal-400 transition-colors">Confirm & Update Profile</button>
                            </div>
                        </div>
'''
html = html.replace(profile_ui_old, profile_ui_new)

# 3C: Add Vue variables and methods for the new features
vue_setup_target = "const activeEngine = ref(null);"
vue_setup_new = """const activeEngine = ref(null);
                const aiExplanation = ref('');
                const selectedFile = ref(null);
                const isParsingResume = ref(false);
                const proposedProfile = ref(null);

                const handleFileUpload = async (event) => {
                    selectedFile.value = event.target.files[0];
                    if (!selectedFile.value) return;
                    isParsingResume.value = true;
                    proposedProfile.value = null;
                    
                    const formData = new FormData();
                    formData.append('file', selectedFile.value);
                    
                    try {
                        const res = await fetch('/api/v1/platform/profile/resume/upload', {
                            method: 'POST',
                            headers: { 'Authorization': `Bearer ${token.value}` },
                            body: formData
                        });
                        const data = await res.json();
                        if(res.ok) proposedProfile.value = data.proposed_updates;
                    } catch(e) { console.error(e); } finally { isParsingResume.value = false; }
                };

                const confirmProfileUpdates = async () => {
                    try {
                        await fetch('/api/v1/platform/profile/resume/confirm', {
                            method: 'POST',
                            headers: { 'Authorization': `Bearer ${token.value}`, 'Content-Type': 'application/json' },
                            body: JSON.stringify({ updates: proposedProfile.value })
                        });
                        proposedProfile.value = null;
                        await loadAllData(); // Reload UI to show new verified data
                    } catch(e) { console.error(e); }
                };
"""
html = html.replace(vue_setup_target, vue_setup_new)

# 3D: Ensure AI explanation is stored from API response
eval_success_target = "evaluationState.value = data.status;"
eval_success_new = "evaluationState.value = data.status; aiExplanation.value = data.ai_explanation;"
html = html.replace(eval_success_target, eval_success_new)

# 3E: Clear AI explanation on close
eval_close_target = "evaluationState.value = 'pending';"
eval_close_new = "evaluationState.value = 'pending'; aiExplanation.value = '';"
html = html.replace(eval_close_target, eval_close_new)

# 3F: Return new variables in Vue setup
return_target = "return { currentView,"
return_new = "return { currentView, aiExplanation, handleFileUpload, isParsingResume, proposedProfile, confirmProfileUpdates,"
html = html.replace(return_target, return_new)

with open(html_path, "w") as f:
    f.write(html)

for path, content in FILES.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
