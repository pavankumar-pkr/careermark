from datetime import datetime
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

class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipient_email = Column(String)
    subject = Column(String)
    body = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
