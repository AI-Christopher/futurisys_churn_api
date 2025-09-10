# tests/conftest.py
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

# Par défaut, pas de DB pendant les tests d'API unitaires
os.environ.setdefault("DATABASE_ENABLED", "false")

DATASET_PATH = Path(os.environ.get("TEST_DATASET_PATH", "data/data_employees.csv"))
MODEL_PATH = Path("models/churn_model.joblib")
FEATURES_PATH = Path("models/input_features.json")


@pytest.fixture(scope="module")
def client_no_db():
    """
    Client authentifié via override (sans BDD).
    """
    os.environ["DATABASE_ENABLED"] = "false"

    from futurisys_churn_api.api.endpoints import auth, prediction
    importlib.reload(db_conn)
    importlib.reload(sec)          # relit l'env (API_KEY, etc.)
    importlib.reload(auth)
    importlib.reload(prediction)

    # 1) client éphémère pour récupérer un token
    c = TestClient(app)
    r = c.post("/auth/token", data={"username": "futurisys_user", "password": "futurisys_password"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    # 2) client avec headers par défaut
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    yield client

    # nettoyage
    del os.environ["DATABASE_ENABLED"]
    importlib.reload(db_conn)


@pytest.fixture(scope="function")
def client_with_db():
    """
    Crée une BDD SQLite + client authentifié (vraie auth) et nettoie.
    """
    db_file = Path(__file__).parent / "_tmp_api.db"

    # Fermer proprement toute ancienne connexion avant suppression (Windows)
    close_all_sessions()
    try:
        if db_conn.engine:
            db_conn.engine.dispose()
    except Exception:
        pass
    if db_file.exists():
        try:
            db_file.unlink()
        except PermissionError:
            # dernier recours : renommer si verrouillé (rare sous Windows)
            db_file.rename(db_file.with_suffix(".db.bak"))

    os.environ["DATABASE_ENABLED"] = "true"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file.as_posix()}"

    from futurisys_churn_api.api.endpoints import auth, prediction
    importlib.reload(db_conn)
    importlib.reload(sec)          # relit l'env
    importlib.reload(auth)
    importlib.reload(prediction)

    # IMPORTANT : importer le module models pour enregistrer les tables sur Base
    # puis créer les tables via la même Base
    db_models.Base.metadata.create_all(bind=db_conn.engine)

    # 1) client éphémère pour créer l’utilisateur + récupérer un token
    c = TestClient(app)
    c.post("/auth/register", params={"email": "test@db.com", "password": "password"})
    r = c.post("/auth/token", data={"username": "test@db.com", "password": "password"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    # 2) client avec headers par défaut
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    yield client

    # Nettoyage
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


@pytest.fixture(scope="session")
def dataset_df() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        pytest.skip(f"Dataset absent: {DATASET_PATH}")
    return pd.read_csv(DATASET_PATH)


@pytest.fixture(scope="session")
def model_available() -> bool:
    return MODEL_PATH.exists() and FEATURES_PATH.exists()


@pytest.fixture(scope="session")
def sample_payload() -> dict:
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
