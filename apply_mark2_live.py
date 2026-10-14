import os

FILES = {}

# Upgrade to Real SMTP Email
FILES["core/notifications.py"] = '''import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from sqlalchemy.orm import Session
from db.models import NotificationOutbox

class EmailAdapter:
    @staticmethod
    def send_email(to_address: str, subject: str, body: str) -> bool:
        smtp_user = os.getenv("SMTP_USERNAME")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        
        if not smtp_user or not smtp_pass:
            print(f"\\n[MOCK EMAIL - No SMTP config] To: {to_address} | Sub: {subject}")
            return True
            
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = to_address
        
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            print(f"\\n[LIVE EMAIL SENT] Successfully delivered to {to_address}")
            return True
        except Exception as e:
            print(f"\\n[EMAIL FAILED] Error: {e}")
            return False

class NotificationService:
    @staticmethod
    def process_outbox(db: Session):
        pending_jobs = db.query(NotificationOutbox).filter(NotificationOutbox.status == "pending").all()
        for job in pending_jobs:
            success = EmailAdapter.send_email(job.recipient_email, job.subject, job.body)
            job.status = "sent" if success else "failed"
            job.processed_at = datetime.utcnow()
        db.commit()
'''

# Create the Live Web Scraper
FILES["scripts/scrape_jobs.py"] = '''import sys, os
import requests
from bs4 import BeautifulSoup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import SessionLocal
from db.models import Opportunity

def scrape_and_load():
    print("Fetching live job data...")
    # Using an open-source sandbox job board for safe scraping
    url = "https://realpython.github.io/fake-jobs/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    db = SessionLocal()
    jobs = soup.find_all("div", class_="card-content")
    count = 0
    
    for job in jobs[:5]:  # Scrape the first 5 recent postings
        title = job.find("h2", class_="title").text.strip()
        company = job.find("h3", class_="company").text.strip()
        
        existing = db.query(Opportunity).filter(Opportunity.title == title).first()
        if not existing:
            new_opp = Opportunity(
                title=title,
                organization=company,
                description=f"Live scraped posting for {title} at {company}.",
                # Applying standard B.Tech CS rules for testing
                requirements={"degree": "B.Tech", "branch": "Computer Science"} 
            )
            db.add(new_opp)
            count += 1
            
    db.commit()
    print(f"Successfully scraped and added {count} new live jobs to the database!")
    db.close()

if __name__ == "__main__":
    scrape_and_load()
'''

for path, content in FILES.items():
    with open(path, "w") as f:
        f.write(content)

print("Mark 2 Live code injected successfully!")
