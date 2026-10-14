import sys, os
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
