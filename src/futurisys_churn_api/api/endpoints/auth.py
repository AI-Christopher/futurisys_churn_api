"""
Endpoints d'authentification (inscription + obtention de token JWT).

Résumé
------
- POST /auth/register  : crée un utilisateur **uniquement si une base de données est active**.
  - BDD off => 503 ; email doublon => 400 ; succès => 201 avec {id, email, role}.
- POST /auth/token     : login minimal via formulaire (username + password) → JWT.
  - Avec BDD : vérifie l'utilisateur en base.
  - Sans BDD : fallback sur `fake_users_db` (mode démo/tests).
  - Identifiants invalides => 400 (conforme aux tests).
  - Scopes dans le JWT selon le rôle (viewer/analyst/admin).

Note Swagger
------------
La fenêtre "Authorize" de Swagger utilise un modal OAuth2 générique et peut afficher
`client_id` / `client_secret`. **Ignorez ces champs** dans ce projet : seuls
`username` et `password` sont utilisés.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session

from ..security import (
    get_db,
    get_password_hash,
    verify_password,
    create_access_token,
    fake_users_db,  # fallback si la BDD est désactivée
    User,           # modèle SQLAlchemy (importé via security)
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    email: str,
    password: str,
    role: str = "viewer",
    db: Session = Depends(get_db),
):
    """
    Inscrit un nouvel utilisateur (BDD requise).

    - 503 si la base est désactivée.
    - 400 si l'email est déjà enregistré.
    - 201 avec {id, email, role} en cas de succès.
    """
    if not db:
        raise HTTPException(status_code=503, detail="La création de compte est désactivée.")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà enregistré.")

    user = User(email=email, hashed_password=get_password_hash(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/token")
def login(
    # ⬇️ Formulaire minimal (Swagger affichera uniquement ces deux champs ici)
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Authentifie l'utilisateur et retourne un JWT.

    - Avec BDD : recherche par email (= username) et vérification du hash.
    - Sans BDD : fallback sur `fake_users_db`.
    - 400 si identifiants invalides.
    - Scopes ajoutés au JWT selon le rôle.
    """
    user_data = None

    if db:
        # Mode AVEC base de données
        user_in_db = db.query(User).filter(User.email == username).first()
        if user_in_db and verify_password(password, user_in_db.hashed_password):
            user_data = user_in_db
    else:
        # Mode SANS base de données (démo/tests)
        user_dict = fake_users_db.get(username)
        if user_dict and verify_password(password, user_dict["hashed_password"]):
            user_data = User(**user_dict)

    if not user_data:
        # 400 (et non 401) pour coller aux tests existants
        raise HTTPException(status_code=400, detail="Nom d'utilisateur ou mot de passe incorrect.")

    # Attribution des scopes selon le rôle
    scopes = ["predict:read"]
    if user_data.role in ("analyst", "admin"):
        scopes.append("predict:write")
    if user_data.role == "admin":
        scopes.append("admin")

    access_token = create_access_token(subject=user_data.email, scopes=scopes)
    return {"access_token": access_token, "token_type": "bearer"}
