# tests/conftest.py
import os
from pathlib import Path
import json
import pandas as pd
import pytest

# Par défaut, pas de DB pendant les tests d'API unitaires
os.environ.setdefault("DATABASE_ENABLED", "false")

# Où est ton dataset ? (modifiable via variable d'env)
DATASET_PATH = Path(os.environ.get("TEST_DATASET_PATH", "tests/data/employees_sample.csv"))

# Où est ton modèle ?
MODEL_PATH = Path("models/churn_model.joblib")
FEATURES_PATH = Path("models/input_features.json")

@pytest.fixture(scope="session")
def dataset_df() -> pd.DataFrame:
    """
    Charge le dataset si présent (sert aux tests 'dataset').
    Les tests qui en dépendent peuvent le skipper si absent.
    """
    if not DATASET_PATH.exists():
        pytest.skip(f"Dataset absent: {DATASET_PATH}")
    return pd.read_csv(DATASET_PATH)

@pytest.fixture(scope="session")
def model_available() -> bool:
    """
    Indique si le modèle et le fichier de features sont présents.
    Permet de skip cleanement les tests d'API si besoin.
    """
    return MODEL_PATH.exists() and FEATURES_PATH.exists()

@pytest.fixture(scope="session")
def sample_payload() -> dict:
    """
    Payload BRUT conforme à futurisys_churn_api.api.schemas.EmployeeData
    (ne dépend pas du dataset).
    """
    return {
        "age": 35,
        "revenu_mensuel": 5000,
        "nombre_experiences_precedentes": 2,
        "annee_experience_totale": 10,
        "annees_dans_l_entreprise": 5,
        "annees_dans_le_poste_actuel": 3,
        "annees_depuis_la_derniere_promotion": 1,
        "annes_sous_responsable_actuel": 2,
        "satisfaction_employee_environnement": 3,
        "note_evaluation_precedente": 3,
        "niveau_hierarchique_poste": 2,
        "satisfaction_employee_nature_travail": 4,
        "satisfaction_employee_equipe": 3,
        "satisfaction_employee_equilibre_pro_perso": 2,
        "note_evaluation_actuelle": 4,
        "augementation_salaire_precedente": 15,
        "nombre_participation_pee": 1,
        "nb_formations_suivies": 3,
        "nombre_employee_sous_responsabilite": 4,
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
