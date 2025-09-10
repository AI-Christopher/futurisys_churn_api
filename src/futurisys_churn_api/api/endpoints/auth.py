# Fichier à modifier : src/futurisys_churn_api/api/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from ..security import (
    get_db,
    get_password_hash,
    verify_password,
    create_access_token,
    fake_users_db, # On en a besoin pour la partie login sans BDD
    User
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(email: str, password: str, role: str = "viewer", db: Session = Depends(get_db)):
    if not db:
        raise HTTPException(status_code=503, detail="La création de compte est désactivée.")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email déjà enregistré.")
    
    user = User(email=email, hashed_password=get_password_hash(password), role=role)
    db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_data = None
    if db:
        # Mode avec BDD
        user_in_db = db.query(User).filter(User.email == form.username).first()
        if user_in_db and verify_password(form.password, user_in_db.hashed_password):
            user_data = user_in_db
    else:
        # Mode sans BDD
        user_dict = fake_users_db.get(form.username)
        if user_dict and verify_password(form.password, user_dict["hashed_password"]):
            user_data = User(**user_dict)

    if not user_data:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Nom d'utilisateur ou mot de passe incorrect.")

    # Scopes
    scopes = ["predict:read"]
    if user_data.role in ("analyst", "admin"):
        scopes.append("predict:write")
    if user_data.role == "admin":
        scopes.append("admin")
    
    access_token = create_access_token(subject=user_data.email, scopes=scopes)
    return {"access_token": access_token, "token_type": "bearer"}