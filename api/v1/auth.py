from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from db.database import get_db
from db.models import User
from core.security import verify_password, create_access_token

router = APIRouter()

# Setup password hashing for new users
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# The URL Swagger will use to authenticate
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Schema for creating a new user
class UserCreate(BaseModel):
    email: str
    password: str

@router.post("/signup")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # 1. Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 2. Hash the password and save the new user to the database
    hashed_pwd = pwd_context.hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    
    return {"message": "User successfully created!", "email": user.email}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Check email against database
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Verify password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="AUTHORIZATION DENIED: Invalid Credentials.")
    
    # Return JWT Token
    return {
        "access_token": create_access_token({"sub": user.email}), 
        "token_type": "bearer"
    }