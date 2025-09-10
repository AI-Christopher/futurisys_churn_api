# tests/test_api_predict.py
import pytest
from fastapi.testclient import TestClient

# DB OFF pour ces tests
#os.environ["DATABASE_ENABLED"] = "false"

from futurisys_churn_api.api.main import app

client = TestClient(app)

@pytest.mark.usefixtures("model_available")
def test_predict_ok_no_db(sample_payload, model_available, client_no_db):
    if not model_available:
        pytest.skip("Modèle non disponible (models/churn_model.joblib ou input_features.json manquant)")

    r = client_no_db.post("/predict", json=sample_payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "prediction" in data and "churn_probability" in data
    assert data["prediction"] in (0, 1)
    assert 0 <= data["churn_probability"] <= 1


@pytest.mark.parametrize("poste", [
    "Cadre Commercial", "Assistant de Direction", "Consultant",
    "Tech Lead", "Manager", "Senior Manager",
    "Représentant Commercial", "Directeur Technique", "Ressources Humaines",
])
def test_predict_ok_for_all_valid_postes(sample_payload, model_available, client_no_db, poste):
    if not model_available:
        pytest.skip("Modèle non disponible")

    payload = {**sample_payload, "poste": poste}
    r = client_no_db.post("/predict", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "prediction" in data and "churn_probability" in data