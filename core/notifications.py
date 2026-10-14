import os
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
            print(f"\n[MOCK EMAIL - No SMTP config] To: {to_address} | Sub: {subject}")
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
            print(f"\n[LIVE EMAIL SENT] Successfully delivered to {to_address}")
            return True
        except Exception as e:
            print(f"\n[EMAIL FAILED] Error: {e}")
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
