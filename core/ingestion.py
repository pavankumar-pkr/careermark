import hashlib
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
