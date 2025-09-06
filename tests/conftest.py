# tests/conftest.py
import os
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest

# Désactive la BDD par défaut pour les tests API unitaires
os.environ.setdefault("DATABASE_ENABLED", "false")

# Point d'entrée du dataset : variable d'env ou fallback
DATASET_PATH = Path(os.environ.get("TEST_DATASET_PATH", "tests/data/employees_sample.csv"))

@pytest.fixture(scope="session")
def dataset_df() -> pd.DataFrame:
    """Charge le dataset une seule fois pour toute la session de tests."""
    df = pd.read_csv(DATASET_PATH)
    return df

@pytest.fixture(scope="session")
def model_features() -> list:
    """Charge la liste des colonnes attendues par le modèle."""
    with open("models/input_features.json", "r") as f:
        return json.load(f)

@pytest.fixture
def dummy_model(monkeypatch):
    # Remplace le modèle réel par un stub rapide/déterministe
    class DummyModel:
        def predict(self, X):
            # renvoie toujours 1 (quitte) pour simplifier
            return np.array([1] * len(X))
        def predict_proba(self, X):
            # proba classe 1 = 0.8
            return np.tile(np.array([[0.2, 0.8]]), (len(X), 1))
    # Patch dans le module de l’endpoint
    from futurisys_churn_api.api.endpoints import prediction as pred_mod
    monkeypatch.setattr(pred_mod, "model", DummyModel())
    return True
