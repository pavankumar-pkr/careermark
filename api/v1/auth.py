from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User
from core.security import verify_password, create_access_token

router = APIRouter()

# 1. Define the security scheme for Swagger to use
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

# 2. Use OAuth2PasswordRequestForm to handle Swagger's form data
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Swagger uses the 'username' field, so we check that against the User email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="AUTHORIZATION DENIED: Invalid Credentials.")
    
    # 3. Swagger explicitly expects the token key to be named 'access_token'
    return {
        "access_token": create_access_token({"sub": user.email}), 
        "token_type": "bearer"
    }