from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from db.models import User
from core.security import verify_password, create_access_token

router = APIRouter()
class AuthSchema(BaseModel): email: str; password: str

@router.post("/login")
def login(data: AuthSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="AUTHORIZATION DENIED: Invalid Credentials.")
    return {"token": create_access_token({"sub": user.email})}
