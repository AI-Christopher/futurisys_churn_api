# tests/test_api_predict.py
"""
Tests d’intégration des endpoints de prédiction en **mode sans base de données**.

Ce module vérifie deux choses :
1) /predict fonctionne correctement avec un payload valide (retourne un code 200,
   un champ `prediction` ∈ {0,1} et un `churn_probability` ∈ [0,1]).
2) /predict accepte toutes les valeurs autorisées du champ catégoriel `poste`.

Notes importantes :
- La fixture `client_no_db` (définie dans tests/conftest.py) fournit un client FastAPI
  **déjà authentifié** via un token (mode “fake users” sans BDD).
- La fixture `model_available` skippe proprement si le modèle/les features ne sont
  pas présents (évite les faux échecs).
- La fixture `sample_payload` fournit un payload conforme au schéma `EmployeeData`.
"""

import pytest
from fastapi.testclient import TestClient

# DB OFF pour ces tests (piloté par la fixture client_no_db).
# os.environ["DATABASE_ENABLED"] = "false"

from futurisys_churn_api.api.main import app

# Client “brut” non authentifié (ici non utilisé, on garde l’import pour
# documenter la différence avec la fixture client_no_db qui, elle, est authentifiée).
client = TestClient(app)


@pytest.mark.usefixtures("model_available")
def test_predict_ok_no_db(sample_payload, model_available, client_no_db):
    """
    Vérifie qu’un appel simple à /predict renvoie 200 et une structure de réponse valide
    (prediction + churn_probability), lorsque le modèle est disponible.
    """
    if not model_available:
        pytest.skip("Modèle non disponible (models/churn_model.joblib ou input_features.json manquant)")

    # Appel avec le client pré-authentifié fourni par la fixture.
    r = client_no_db.post("/predict", json=sample_payload)
    assert r.status_code == 200, r.text

    data = r.json()
    # Les deux champs clés doivent être présents
    assert "prediction" in data and "churn_probability" in data
    # Sanity checks sur les valeurs
    assert data["prediction"] in (0, 1)
    assert 0 <= data["churn_probability"] <= 1


@pytest.mark.parametrize(
    "poste",
    [
        "Cadre Commercial", "Assistant de Direction", "Consultant",
        "Tech Lead", "Manager", "Senior Manager",
        "Représentant Commercial", "Directeur Technique", "Ressources Humaines",
    ],
)
def test_predict_ok_for_all_valid_postes(sample_payload, model_available, client_no_db, poste):
    """
    Vérifie que l’API accepte chacune des valeurs autorisées pour le champ `poste`.
    Chaque valeur est testée indépendamment grâce à `parametrize`.
    """
    if not model_available:
        pytest.skip("Modèle non disponible")

    # On clone le payload d’exemple et on remplace uniquement le poste.
    payload = {**sample_payload, "poste": poste}

    r = client_no_db.post("/predict", json=payload)
    assert r.status_code == 200, r.text

    data = r.json()
    # La réponse doit toujours contenir les champs clés
    assert "prediction" in data and "churn_probability" in data
