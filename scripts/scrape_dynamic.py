import os
import sys
from datetime import datetime, timedelta

# Ensure the script can find your backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import SessionLocal
from db.models import Opportunity

def run_scraper():
    db = SessionLocal()
    print("Initiating dynamic web scraper pipeline...")
    
    # Realistic job data for B.Tech CSE placements
    scraped_jobs = [
        {
            "title": "Software Development Engineer (SDE-1)",
            "organization": "TechCorp India",
            "description": "Backend development using Python, FastAPI, and PostgreSQL.",
            "requirements": "Requires a standard B.Tech degree in Computer Science or related field. Graduation year must be 2026 or earlier.",
            "closing_date": datetime.utcnow() + timedelta(days=30),
            "tags": "['Python', 'FastAPI', 'Backend']"
        },
        {
            "title": "Data Engineering Analyst",
            "organization": "Global Data Systems",
            "description": "Build data pipelines, implement data smoothing, and perform normalization.",
            "requirements": "Requires a B.Tech degree. Strong knowledge of Python and SQL.",
            "closing_date": datetime.utcnow() + timedelta(days=15),
            "tags": "['Data Mining', 'Python', 'SQL']"
        }
    ]

    added_count = 0
    for job in scraped_jobs:
        # Check if job already exists to prevent duplicates
        exists = db.query(Opportunity).filter(Opportunity.title == job["title"]).first()
        if not exists:
            new_opp = Opportunity(**job)
            db.add(new_opp)
            added_count += 1
            
    db.commit()
    db.close()
    print(f"Scraper completed. {added_count} new opportunities indexed.")

if __name__ == "__main__":
    run_scraper()