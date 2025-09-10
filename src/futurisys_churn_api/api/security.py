# Fichier à modifier : src/futurisys_churn_api/api/security.py

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..database.connection import SessionLocal
from ..database.models import User

# --- Configuration ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "une_cle_secrete_tres_complexe")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60
API_KEY = os.getenv("API_KEY")

# --- Outils ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={"predict:read": "Lire des prédictions", "predict:write": "Créer des prédictions", "admin": "Admin"}
)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# --- Base de données factice ---
fake_users_db = {
    "futurisys_user": {
        "email": "futurisys_user",
        "hashed_password": pwd_context.hash("futurisys_password"),
        "role": "admin",
        "is_active": True
    }
}

# --- Fonctions Utilitaires ---
def get_password_hash(password: str) -> str: return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool: return pwd_context.verify(plain_password, hashed_password)

def get_db():
    if SessionLocal is None:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(subject: str, scopes: List[str] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire, "scopes": scopes or []}
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

# --- Dépendance d'Authentification Principale ---
async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: Optional[str] = payload.get("sub")
        token_scopes: List[str] = payload.get("scopes", [])
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = None
    if db:
        # Mode AVEC BDD
        user = db.query(User).filter(User.email == username).first()
    else:
        # Mode SANS BDD
        user_dict = fake_users_db.get(username)
        if user_dict:
            user = User(**user_dict) # Crée un objet User à la volée

    if user is None or not user.is_active:
        raise credentials_exception

    # Vérification des scopes
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    return user

async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    if API_KEY is None: return
    if not api_key or not secrets.compare_digest(api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API Key")