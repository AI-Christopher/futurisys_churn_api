from fastapi.testclient import TestClient
from futurisys_api.api.main import app # On importe notre application FastAPI

client = TestClient(app)

def test_read_main():
    """
    Teste si la route racine ("/") de l'API fonctionne et retourne un statut 200.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API de prédiction de turnover - Futurisys"}