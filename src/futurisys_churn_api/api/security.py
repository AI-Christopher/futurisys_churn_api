"""
Sécurité & Authentification pour Futurisys Churn API.

Fonctionnalités couvertes :
- Hachage / vérification de mots de passe (Passlib + bcrypt)
- Création et validation de JWT (jose)
- OAuth2 (flux "password") via FastAPI (OAuth2PasswordBearer)
- Récupération de l'utilisateur courant avec vérification des scopes
- Vérification d'une API Key (en-tête HTTP `X-API-Key`) optionnelle

Notes d'implémentation
----------------------
- Base de données optionnelle :
  - Si `SessionLocal` est indisponible (ex: mode déployé sans DB), on passe
    en mode "fake DB" via `fake_users_db`.
- API Key :
  - `verify_api_key()` relit `API_KEY` dans l'environnement **à chaque requête**,
    ce qui permet de l'activer/désactiver dynamiquement (utile en tests).
  - Pour que FastAPI ne mette pas en cache la dépendance, déclare-la côté
    endpoint avec `Security(verify_api_key, use_cache=False)`.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..database.connection import SessionLocal
from ..database.models import User

# --- Configuration JWT ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "une_cle_secrete_tres_complexe")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60

# Contexte de hachage (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 "Password" avec scopes
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={
        "predict:read": "Lire des prédictions",
        "predict:write": "Créer des prédictions",
        "admin": "Admin"
    }
)

# --- Base d'utilisateurs factice (mode sans BDD) ---
# NB: le hachage est fait au chargement du module.
fake_users_db = {
    "futurisys_user": {
        "email": "futurisys_user",
        "hashed_password": pwd_context.hash("futurisys_password"),
        "role": "admin",
        "is_active": True
    }
}


# --------------------------
# Utilitaires mot de passe
# --------------------------
def get_password_hash(pw: str) -> str:
    """Retourne le hachage `bcrypt` du mot de passe en clair `pw`."""
    return pwd_context.hash(pw)


def verify_password(plain: str, hashed: str) -> bool: 
    """Vérifie qu'un mot de passe en clair `plain` correspond au hachage `hashed`."""
    return pwd_context.verify(plain, hashed)

# --------------------------
# Accès Base de données
# --------------------------
def get_db():
    """
    Dépendance FastAPI : ouvre une session DB si possible, sinon yield None.

    Ce design permet de faire tourner l'API en mode "sans BDD" (ex: Spaces),
    tout en conservant la même signature de dépendance côté endpoints.
    """
    if SessionLocal is None:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------
# JWT
# --------------------------
def create_access_token(subject: str, scopes: List[str] = None) -> str:
    """
    Crée un JWT signé contenant :
    - `sub` : l'identifiant (ici l'email) du user
    - `exp` : date d'expiration
    - `scopes` : liste des scopes accordés (ex: ["predict:read"])
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire, "scopes": scopes or []}
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# --------------------------
# Authentification principale
# --------------------------
async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Récupère l'utilisateur courant depuis le JWT `token`, puis :
      1) Si DB dispo, charge l'utilisateur en base ; sinon, cherche dans `fake_users_db`.
      2) Vérifie que l'utilisateur est actif.
      3) Vérifie la présence de tous les `security_scopes.scopes` dans le token.

    Lève 401 si le token est invalide ou l'utilisateur inexistant/inactif.
    Lève 403 si les scopes sont insuffisants.
    """
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Décodage du token
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        token_scopes = payload.get("scopes", [])
        if sub is None:
            raise cred_exc
    except JWTError:
        raise cred_exc

    # Recherche de l'utilisateur
    user = None
    if db:
        user = db.query(User).filter(User.email == sub).first()
    else:
        u = fake_users_db.get(sub)
        if u:
            # On construit un objet "User-like" ; ses attributs (role, is_active)
            # sont utilisés par le reste de l'app.
            user = User(**u)

    # Vérifications d'état et de permissions
    if user is None or not user.is_active:
        raise cred_exc

    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    return user

# --------------------------
# API Key optionnelle
# --------------------------
async def verify_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    """
    Vérifie la présence et la validité d'une API Key dans l'en-tête `X-API-Key`.

    Comportement :
    - Si la variable d'env `API_KEY` est **absente**, la vérification est désactivée.
    - Si `API_KEY` est définie :
        - Absence d'en-tête ou valeur incorrecte -> 401
        - Correspondance exacte -> OK

    Astuce FastAPI :
    - Côté endpoint, utilisez `Security(verify_api_key, use_cache=False)` pour éviter
      la mise en cache de la dépendance et relire l’ENV à chaque requête.
    """
    required = os.getenv("API_KEY")  # relecture dynamique (utile en tests)
    if required is None:
        # Pas d'API Key imposée => on n'applique pas de restriction
        return
    
    # Comparaison sûre (contre timing attacks)
    if not x_api_key or not secrets.compare_digest(x_api_key, required):
        raise HTTPException(status_code=401, detail="Invalid API Key")
