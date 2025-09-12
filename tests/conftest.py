"""
Fichier de configuration Pytest (chargé automatiquement par pytest).

Il définit des *fixtures* réutilisables pour tous les tests :
- client_no_db : client d'API authentifié, sans base de données (mode "mock").
- client_with_db : client d'API authentifié, avec base SQLite jetable par test.
- dataset_df : charge le dataset de test si disponible.
- model_available : indique si les artefacts ML (modèle + features) sont présents.
- sample_payload : payload d'exemple conforme au schéma Pydantic EmployeeData.

Notes importantes :
- On manipule des variables d'environnement (DATABASE_ENABLED, DATABASE_URL)
  et on *reload* certains modules pour qu'ils prennent en compte ces valeurs.
- Sous Windows, SQLite peut garder un verrou sur le fichier : on ferme proprement
  les sessions et on gère la suppression avec précaution.
"""

import os
from pathlib import Path
import importlib

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import close_all_sessions

from futurisys_churn_api.api.main import app
from futurisys_churn_api.api import security as sec
from futurisys_churn_api.database import connection as db_conn
from futurisys_churn_api.database import models as db_models

# ------------------------------
# Réglages "globaux" pour les tests
# ------------------------------

# Par défaut, on exécute les tests d’API *sans* base de données.
# (les tests qui veulent une BDD explicite utiliseront client_with_db)
os.environ.setdefault("DATABASE_ENABLED", "false")

# Emplacements par défaut des fichiers de données / artefacts du modèle
DATASET_PATH = Path(os.environ.get("TEST_DATASET_PATH", "data/data_employees.csv"))
MODEL_PATH = Path("models/churn_model.joblib")
FEATURES_PATH = Path("models/input_features.json")


# ------------------------------
# FIXTURE: client_no_db
# ------------------------------
@pytest.fixture(scope="module")
def client_no_db():
    """
    Client FastAPI authentifié avec *token*, pour un environnement SANS base de données.

    Pourquoi on recharge (importlib.reload) ?
    - Les modules lisent les variables d'environnement au *import* (ex: connexion DB, API_KEY).
    - On force leur relecture après avoir positionné DATABASE_ENABLED="false".

    Étapes :
    1) Positionner l'env sans BDD et recharger la stack (conn, security, endpoints)
    2) Ouvrir un client "éphémère" pour obtenir un token (utilisateur factice 'futurisys_user')
    3) Créer un client avec l'en-tête Authorization par défaut (Bearer <token>)
    4) Rendre le client aux tests (yield), puis nettoyer à la fin.
    """
    os.environ["DATABASE_ENABLED"] = "false"

    from futurisys_churn_api.api.endpoints import auth, prediction
    importlib.reload(db_conn)   # Recrée la connexion (ici: None, car DB off)
    importlib.reload(sec)       # Relit l'env (ex: API_KEY) si modifiée par des tests
    importlib.reload(auth)
    importlib.reload(prediction)

    # 1) Récupère un token via l'utilisateur "factice" sans DB
    c = TestClient(app)
    r = c.post("/auth/token", data={"username": "futurisys_user", "password": "futurisys_password"})
    assert r.status_code == 200, "Impossible d'obtenir un token en mode sans BDD"
    token = r.json()["access_token"]

    # 2) Client permanent du module, avec Authorization par défaut
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    yield client

    # Teardown : on remet l'état comme avant et on recharge la connexion
    del os.environ["DATABASE_ENABLED"]
    importlib.reload(db_conn)


# ------------------------------
# FIXTURE: client_with_db
# ------------------------------
@pytest.fixture(scope="function")
def client_with_db():
    """
    Client FastAPI authentifié avec *token*, pour un environnement AVEC base SQLite jetable.

    Chaque test reçoit sa propre base de données (fichier _tmp_api.db) :
    - On ferme les sessions SQLAlchemy en cours et on libère l'engine (Windows aime bien).
    - On supprime le fichier s'il existe déjà (ou on le renomme si verrouillé).
    - On définit DATABASE_ENABLED="true" et DATABASE_URL=sqlite:///<fichier>.
    - On *reload* la connexion/ sécurité / endpoints, puis on crée les tables.
    - On crée un utilisateur réel, obtient un token, et on retourne un client pré-authentifié.

    Le scope=function garantit un environnement propre à chaque test.
    """
    db_file = Path(__file__).parent / "_tmp_api.db"

    # Fermer proprement toute ancienne connexion avant suppression (Windows)
    close_all_sessions()
    try:
        if db_conn.engine:
            db_conn.engine.dispose()
    except Exception:
        pass

    # Supprime le fichier (ou tente un rename en secours si verrouillé)
    if db_file.exists():
        try:
            db_file.unlink()
        except PermissionError:
            db_file.rename(db_file.with_suffix(".db.bak"))

    # Active et configure la BDD
    os.environ["DATABASE_ENABLED"] = "true"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file.as_posix()}"

    # Recharge les modules qui dépendent de la config DB/API
    from futurisys_churn_api.api.endpoints import auth, prediction
    importlib.reload(db_conn)   # Recrée engine + SessionLocal
    importlib.reload(sec)
    importlib.reload(auth)
    importlib.reload(prediction)

    # Crée physiquement les tables sur l'engine courant
    db_models.Base.metadata.create_all(bind=db_conn.engine)

    # Utilisateur réel + token
    c = TestClient(app)
    c.post("/auth/register", params={"email": "test@db.com", "password": "password"})
    r = c.post("/auth/token", data={"username": "test@db.com", "password": "password"})
    assert r.status_code == 200, "Impossible d'obtenir un token en mode avec BDD"
    token = r.json()["access_token"]

    # Client pré-authentifié pour le test
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    yield client

    # Teardown : on ferme, on libère, on supprime le fichier et on nettoie l'env
    close_all_sessions()
    if db_conn.engine:
        db_conn.engine.dispose()
    if db_file.exists():
        try:
            db_file.unlink()
        except PermissionError:
            pass

    del os.environ["DATABASE_ENABLED"]
    del os.environ["DATABASE_URL"]
    importlib.reload(db_conn)


# ------------------------------
# FIXTURE: dataset_df
# ------------------------------
@pytest.fixture(scope="session")
def dataset_df() -> pd.DataFrame:
    """
    Charge le dataset depuis DATASET_PATH.
    Si absent, on "skip" proprement les tests qui en dépendent.
    """
    if not DATASET_PATH.exists():
        pytest.skip(f"Dataset absent: {DATASET_PATH}")
    return pd.read_csv(DATASET_PATH)


# ------------------------------
# FIXTURE: model_available
# ------------------------------
@pytest.fixture(scope="session")
def model_available() -> bool:
    """
    Retourne True si le modèle (joblib) ET la liste de features (JSON) existent.
    Permet de sauter proprement les tests d'API si les artefacts ne sont pas présents.
    """
    return MODEL_PATH.exists() and FEATURES_PATH.exists()


# ------------------------------
# FIXTURE: sample_payload
# ------------------------------
@pytest.fixture(scope="session")
def sample_payload() -> dict:
    """
    Payload d'exemple valide pour /predict.
    Correspond aux champs attendus par le schéma Pydantic EmployeeData.
    """
    return {
        "age": 20,
        "revenu_mensuel": 2500,
        "nombre_experiences_precedentes": 2,
        "annees_dans_l_entreprise": 5,
        "annees_depuis_la_derniere_promotion": 1,
        "satisfaction_employee_environnement": 3,
        "note_evaluation_precedente": 3,
        "satisfaction_employee_nature_travail": 4,
        "satisfaction_employee_equipe": 3,
        "satisfaction_employee_equilibre_pro_perso": 2,
        "augementation_salaire_precedente": 15,
        "nombre_participation_pee": 1,
        "nb_formations_suivies": 3,
        "distance_domicile_travail": 10,
        "niveau_education": 4,
        "genre": "F",
        "frequence_deplacement": "Frequent",
        "poste": "Manager",
        "statut_marital": "Marié(e)",
        "departement": "Consulting",
        "domaine_etude": "Transformation Digitale",
        "heure_supplementaires": "Oui",
    }