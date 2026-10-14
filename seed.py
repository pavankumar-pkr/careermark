import sys
from datetime import datetime, timedelta
from services.api.database import SessionLocal, Base, engine
from services.api.models import User, UserProfile, Opportunity, Application, Notification, ResourcePlaylist
from services.api.auth import get_password_hash

Base.metadata.create_all(bind=engine)
db = SessionLocal()

db.query(Notification).delete()
db.query(Application).delete()
db.query(ResourcePlaylist).delete()
db.query(Opportunity).delete()
db.query(UserProfile).delete()
db.query(User).delete()

user = User(email="pavan@careermark.local", hashed_password=get_password_hash("password123"))
db.add(user)
db.flush()

profile = UserProfile(
    user_id=user.id, full_name="Boyini Pavan Kumar", institution="Vardhaman College of Engineering", 
    degree="B.Tech", branch="Computer Science and Engineering", graduation_year=2026, age=21, cgpa="8.5"
)
db.add(profile)

urgent_date = datetime.utcnow() + timedelta(days=3)
safe_date = datetime.utcnow() + timedelta(days=45)

opps = [
    Opportunity(title="Scientist 'B' (Cyber Security)", organization="NIC", opp_type="Gov", location="Pan-India", closing_date=urgent_date, tags=["Top Pick", "Cyber"], requirements=[{"type": "education", "operator": "in", "value": ["Computer Science and Engineering"], "human_readable": "B.Tech in CSE"}]),
    Opportunity(title="SDE-1 Core Engineering", organization="Amazon", opp_type="Private", location="Hyderabad", closing_date=safe_date, tags=["Trending", "Local"], requirements=[{"type": "graduation_year", "operator": "<=", "value": 2026, "human_readable": "Class of 2026"}]),
    Opportunity(title="SBI Asha Scholarship Program", organization="SBI Foundation", opp_type="Scholarship", location="Pan-India", closing_date=safe_date, tags=["Trending"], requirements=[{"type": "education", "operator": "in", "value": ["Computer Science and Engineering"], "human_readable": "Tech Degree"}])
]
db.add_all(opps)
db.flush()

db.add(Application(user_id=user.id, opportunity_id=opps[0].id, status="Preparation Active"))
db.add(Application(user_id=user.id, opportunity_id=opps[2].id, status="Application Submitted"))
db.add(ResourcePlaylist(target_skill="Advanced Algorithms", provider="NPTEL", course_name="Design and Analysis of Algorithms"))
db.add(ResourcePlaylist(target_skill="Cyber Security", provider="PortSwigger", course_name="Web Security Academy"))
db.commit()
print("✅ Phase 11 Seed Data Loaded (Pipeline active).")
