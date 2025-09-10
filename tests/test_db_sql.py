# tests/test_db_sql.py
import pytest

@pytest.mark.usefixtures("model_available")
def test_predict_with_sqlite(client_with_db, sample_payload, model_available):
    """
    Teste que le endpoint /predict enregistre bien les entrées et les sorties
    dans la base de données SQLite configurée par la fixture.
    """
    if not model_available:
        pytest.skip("Modèle non disponible")
    
    # On utilise directement le client authentifié
    response = client_with_db.post("/predict", json=sample_payload)

    # Les assertions
    # Assertions sur la réponse API
    assert response.status_code == 200
    data = response.json()
    assert "prediction_id" in data
    assert "input_id" in data
    assert data["prediction_id"] == 1 # C'est la première prédiction
    assert data["input_id"] == 1 # C'est la première entrée
    