import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta
from db.database import SessionLocal, Base, engine
from db.models import User, UserProfile, Opportunity, Application, Requirement, VerificationAudit
from core.security import get_password_hash

Base.metadata.create_all(bind=engine)
db = SessionLocal()

db.query(VerificationAudit).delete()
db.query(Requirement).delete()
db.query(Application).delete()
db.query(Opportunity).delete()
db.query(UserProfile).delete()
db.query(User).delete()

user = User(email="candidate@careermark.local", hashed_password=get_password_hash("password123"))
db.add(user)
db.flush()

# Note: The profile deliberately lacks an 'age' attribute to test CANNOT_VERIFY
profile = UserProfile(user_id=user.id, full_name="Candidate Node 1", institution="Engineering Institute", degree="B.Tech", branch="Computer Science", graduation_year=2026)
db.add(profile)

urgent = datetime.utcnow() + timedelta(days=3)
opp1 = Opportunity(title="Scientist 'B'", organization="NIC", opp_type="Gov", location="Pan-India", closing_date=urgent, tags=["Top Pick", "Cyber"])
opp2 = Opportunity(title="SDE-1", organization="Amazon", opp_type="Private", location="Hyderabad", closing_date=urgent, tags=["Local"])
db.add_all([opp1, opp2])
db.flush()

# NORMALIZED REQUIREMENTS
reqs = [
    # Opp 1 will be ELIGIBLE
    Requirement(opportunity_id=opp1.id, field_name="degree", operator="IN", target_value='["B.Tech", "B.E"]', requirement_text="Requires a standard Tech Degree"),
    Requirement(opportunity_id=opp1.id, field_name="graduation_year", operator="<=", target_value="2026", requirement_text="Must be class of 2026 or earlier"),
    
    # Opp 2 will result in CANNOT_VERIFY because 'age' is missing from the user profile
    Requirement(opportunity_id=opp2.id, field_name="degree", operator="IN", target_value='["B.Tech", "B.E"]', requirement_text="Requires a standard Tech Degree"),
    Requirement(opportunity_id=opp2.id, field_name="age", operator="<=", target_value="25", requirement_text="Maximum age limit is 25 years")
]
db.add_all(reqs)
db.add(Application(user_id=user.id, opportunity_id=opp1.id, status="Target Identified"))
db.commit()
print("✅ Phase 14 Data Seeded: Normalized Requirements Engine Online.")
