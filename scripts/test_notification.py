import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import SessionLocal
from db.models import NotificationOutbox

def run():
    db = SessionLocal()
    job = NotificationOutbox(
        user_id=1,
        recipient_email="chintu2839@gmail.com",
        subject="CareerMark Alert: Senior Python Developer Deadline Approaching",
        body="Hello!\n\nA live-scraped opportunity matching your B.Tech in Computer Science profile closes soon. Log in to CareerMark to review your evaluation."
    )
    db.add(job)
    db.commit()
    print("Notification job queued for chintu2839@gmail.com.")
    db.close()

if __name__ == "__main__":
    run()
