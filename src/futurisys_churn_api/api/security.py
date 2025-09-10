# src/futurisys_churn_api/api/security.py
import os
import secrets
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from ..database.connection import SessionLocal
from ..database.models import User

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "une_cle_secrete_tres_complexe")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={"predict:read": "Lire des prédictions", "predict:write": "Créer des prédictions", "admin": "Admin"}
)

fake_users_db = {
    "futurisys_user": {
        "email": "futurisys_user",
        "hashed_password": pwd_context.hash("futurisys_password"),
        "role": "admin",
        "is_active": True
    }
}

def get_password_hash(pw: str) -> str: return pwd_context.hash(pw)
def verify_password(plain: str, hashed: str) -> bool: return pwd_context.verify(plain, hashed)

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

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        token_scopes = payload.get("scopes", [])
        if sub is None:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = None
    if db:
        user = db.query(User).filter(User.email == sub).first()
    else:
        u = fake_users_db.get(sub)
        if u:
            user = User(**u)

    if user is None or not user.is_active:
        raise cred_exc

    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    return user

# ⬇️ LIRE l’ENV À CHAQUE REQUÊTE + prêter l’en-tête X-API-Key via Header
async def verify_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    required = os.getenv("API_KEY")  # relecture dynamique
    if required is None:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, required):
        raise HTTPException(status_code=401, detail="Invalid API Key")
