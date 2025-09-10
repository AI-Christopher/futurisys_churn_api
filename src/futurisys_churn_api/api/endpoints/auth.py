from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..security import get_db, get_password_hash, verify_password, create_access_token
from ...database.models import User
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(email: str, password: str, role: str = "viewer", db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email already registered")
    user = User(email=email, hashed_password=get_password_hash(password), role=role)
    db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}

@router.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(400, "Incorrect username or password")
    # scopes simples selon rôle
    scopes = ["predict:read"]
    if user.role in ("analyst", "admin"):
        scopes.append("predict:write")
    if user.role == "admin":
        scopes.append("admin")
    access_token = create_access_token(sub=user.email, scopes=scopes)
    return {"access_token": access_token, "token_type": "bearer"}
