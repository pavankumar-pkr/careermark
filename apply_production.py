import os

FILES = {}

# 1. Cloud-Ready Database Config (Switches to Postgres automatically in the cloud)
FILES["db/database.py"] = '''import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./careermark.db")

# Cloud providers often use postgres://, but SQLAlchemy requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs connect_args, Postgres does not
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
'''

# 2. Advanced Dynamic Scraper using Playwright (Handles JavaScript-heavy sites)
FILES["scripts/scrape_dynamic.py"] = '''import sys, os
from playwright.sync_api import sync_playwright
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import SessionLocal
from db.models import Opportunity, Requirement

def scrape_dynamic_jobs():
    print("Launching headless browser for dynamic scraping...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Scraping a dynamic job board (Y Combinator jobs as a live example)
        page.goto("https://www.ycombinator.com/jobs", wait_until="networkidle")
        
        # Wait for the JS job cards to load
        page.wait_for_selector(".job-name", timeout=10000)
        
        job_elements = page.query_selector_all(".job-name")[:5]
        company_elements = page.query_selector_all(".company-name")[:5]
        
        db = SessionLocal()
        count = 0
        
        for job, company in zip(job_elements, company_elements):
            title = job.inner_text().strip()
            org = company.inner_text().strip()
            
            existing = db.query(Opportunity).filter(Opportunity.title == title).first()
            if not existing:
                new_opp = Opportunity(
                    title=title,
                    organization=org,
                    requirements=[
                        Requirement(field_name="degree", operator="==", target_value="B.Tech"),
                        Requirement(field_name="branch", operator="==", target_value="Computer Science")
                    ]
                )
                db.add(new_opp)
                count += 1
                
        db.commit()
        db.close()
        browser.close()
        print(f"Successfully scraped {count} dynamic jobs using Playwright!")

if __name__ == "__main__":
    scrape_dynamic_jobs()
'''

# 3. Infrastructure as Code (render.yaml for one-click cloud deployment)
FILES["render.yaml"] = '''services:
  - type: web
    name: careermark-web
    env: python
    buildCommand: "pip install -r requirements.txt && playwright install chromium"
    startCommand: "uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: careermark-db
          property: connectionString
      - key: GEMINI_API_KEY
        sync: false
      - key: SMTP_USERNAME
        sync: false
      - key: SMTP_PASSWORD
        sync: false
      - key: SECRET_KEY
        generateValue: true

  - type: psql
    name: careermark-db
    plan: free
'''

for path, content in FILES.items():
    with open(path, "w") as f:
        f.write(content)

print("Production upgrades applied successfully!")
