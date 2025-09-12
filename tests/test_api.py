"""
Tests basiques de l’API : vérifie que la route racine ("/") répond bien.

Objectif :
- S’assurer que l’application démarre et qu’un GET "/" renvoie un 200
  accompagné du message JSON attendu.

Remarques :
- Ce test n’a pas besoin d’authentification.
- Il utilise TestClient de FastAPI pour simuler une requête HTTP.
"""

from fastapi.testclient import TestClient
from futurisys_churn_api.api.main import app  # Application FastAPI à tester

# Instancie un client de test isolé (pas de serveur externe nécessaire).
client = TestClient(app)

def test_read_main():
    """
    Vérifie que l’endpoint racine "/" renvoie:
    - un statut HTTP 200
    - le corps JSON {"message": "API de prédiction de turnover - Futurisys"}
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API de prédiction de turnover - Futurisys"}
