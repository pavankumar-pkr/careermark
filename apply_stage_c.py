import os

FILES = {}

FILES["db/models.py"] = '''from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    profiles = relationship("UserProfile", back_populates="user")
    applications = relationship("Application", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    full_name = Column(String)
    institution = Column(String)
    degree = Column(String)
    branch = Column(String)
    graduation_year = Column(Integer)
    age = Column(Integer)
    cgpa = Column(String)
    user = relationship("User", back_populates="profiles")

class SourceRegistry(Base):
    __tablename__ = "source_registry"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    base_url = Column(String)
    source_type = Column(String)
    last_checked = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class OpportunitySnapshot(Base):
    __tablename__ = "opportunity_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("source_registry.id"))
    canonical_url = Column(String, index=True)
    content_hash = Column(String, index=True)
    raw_payload = Column(Text)
    retrieved_at = Column(DateTime, default=datetime.utcnow)
    parsed_successfully = Column(Boolean, default=False)

class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("source_registry.id"), nullable=True)
    title = Column(String, index=True)
    organization = Column(String, index=True)
    opp_type = Column(String) 
    location = Column(String)
    closing_date = Column(DateTime)
    tags = Column(JSON, default=list)
    version = Column(Integer, default=1)
    requirements = relationship("Requirement", back_populates="opportunity")

class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    field_name = Column(String)
    operator = Column(String)
    target_value = Column(String) 
    requirement_text = Column(String)
    opportunity = relationship("Opportunity", back_populates="requirements")

class VerificationAudit(Base):
    __tablename__ = "verification_audits"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    status = Column(String)
    evidence_chain = Column(JSON)
    evaluated_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    status = Column(String, default="Target Identified")
    user = relationship("User", back_populates="applications")
    opportunity = relationship("Opportunity")
'''

FILES["core/ingestion.py"] = '''import hashlib
import json
from datetime import datetime
from sqlalchemy.orm import Session
from db.models import SourceRegistry, OpportunitySnapshot, Opportunity, Requirement

class OfficialSourceAdapter:
    def __init__(self, db: Session):
        self.db = db

    def generate_hash(self, payload: dict) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def ingest_payload(self, source_name: str, canonical_url: str, payload: dict):
        source = self.db.query(SourceRegistry).filter(SourceRegistry.name == source_name).first()
        if not source:
            source = SourceRegistry(name=source_name, base_url=canonical_url, source_type="Official")
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
        
        content_hash = self.generate_hash(payload)
        
        existing_snapshot = self.db.query(OpportunitySnapshot).filter(
            OpportunitySnapshot.canonical_url == canonical_url,
            OpportunitySnapshot.content_hash == content_hash
        ).first()
        
        if existing_snapshot:
            source.last_checked = datetime.utcnow()
            self.db.commit()
            return {"status": "unchanged", "message": "Source content unchanged. Idempotent skip."}
        
        snapshot = OpportunitySnapshot(
            source_id=source.id,
            canonical_url=canonical_url,
            content_hash=content_hash,
            raw_payload=json.dumps(payload),
            parsed_successfully=True
        )
        self.db.add(snapshot)
        
        existing_opp = self.db.query(Opportunity).filter(
            Opportunity.title == payload.get("title"), 
            Opportunity.organization == payload.get("organization")
        ).first()
        
        if existing_opp:
            existing_opp.closing_date = datetime.fromisoformat(payload.get("closing_date"))
            existing_opp.version += 1
            opp = existing_opp
            status = "updated"
        else:
            opp = Opportunity(
                source_id=source.id,
                title=payload.get("title"),
                organization=payload.get("organization"),
                opp_type=payload.get("opp_type"),
                location=payload.get("location"),
                closing_date=datetime.fromisoformat(payload.get("closing_date")),
                tags=payload.get("tags", [])
            )
            self.db.add(opp)
            status = "created"
            
        self.db.flush()
        
        self.db.query(Requirement).filter(Requirement.opportunity_id == opp.id).delete()
        for req_data in payload.get("requirements", []):
            req = Requirement(
                opportunity_id=opp.id,
                field_name=req_data["field_name"],
                operator=req_data["operator"],
                target_value=str(req_data["target_value"]),
                requirement_text=req_data["requirement_text"]
            )
            self.db.add(req)
            
        source.last_checked = datetime.utcnow()
        self.db.commit()
        return {"status": status, "message": f"Opportunity {status} successfully."}
'''

FILES["scripts/run_ingestion.py"] = '''import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta
from db.database import SessionLocal
from core.ingestion import OfficialSourceAdapter

def run():
    db = SessionLocal()
    adapter = OfficialSourceAdapter(db)
    
    urgent = (datetime.utcnow() + timedelta(days=15)).isoformat()
    mock_payload = {
        "title": "Scientist 'B' (Live Scraped)",
        "organization": "NIC Official",
        "opp_type": "Gov",
        "location": "Pan-India",
        "closing_date": urgent,
        "tags": ["Gov", "Verified Source"],
        "requirements": [
            {"field_name": "degree", "operator": "IN", "target_value": '["B.Tech", "B.E"]', "requirement_text": "Must hold B.Tech or B.E degree"},
            {"field_name": "graduation_year", "operator": "<=", "target_value": "2026", "requirement_text": "Graduation year 2026 or earlier"}
        ]
    }
    
    print("Fetching official sources...")
    result = adapter.ingest_payload(
        source_name="NIC Recruitment Portal",
        canonical_url="https://recruitment.nic.in/scientist-b",
        payload=mock_payload
    )
    print(f"Ingestion Run 1: {result}")
    
    print("Fetching again to test idempotency...")
    result2 = adapter.ingest_payload(
        source_name="NIC Recruitment Portal",
        canonical_url="https://recruitment.nic.in/scientist-b",
        payload=mock_payload
    )
    print(f"Ingestion Run 2: {result2}")
    
    db.close()

if __name__ == "__main__":
    run()
'''

for path, content in FILES.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
