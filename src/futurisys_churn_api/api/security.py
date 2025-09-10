import os, secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes, APIKeyHeader
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..database.connection import SessionLocal
from ..database.models import User

# --- Config via env ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")  # set en prod !
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

API_KEY = os.getenv("API_KEY")  # si défini, active la clé API
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# --- Password hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(pw: str) -> str: return pwd_context.hash(pw)
def verify_password(plain: str, hashed: str) -> bool: return pwd_context.verify(plain, hashed)

# --- DB dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- OAuth2 (scopes) ---
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={"predict:read": "Lire des prédictions", "predict:write": "Créer des prédictions", "admin": "Admin"}
)

def create_access_token(sub: str, scopes: Optional[List[str]] = None, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or JWT_EXPIRE_MINUTES)
    to_encode = {"sub": sub, "exp": expire, "scopes": scopes or []}
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    cred_exc = HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        sub: str = payload.get("sub")
        token_scopes: List[str] = payload.get("scopes", [])
        if sub is None:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = db.query(User).filter(User.email == sub).first()
    if not user or not user.is_active:
        raise cred_exc

    # vérifier les scopes requis
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    return user

# --- Clé API (optionnelle) ---
async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    if API_KEY is None:
        return  # pas activé
    if not api_key or not secrets.compare_digest(api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API Key")
