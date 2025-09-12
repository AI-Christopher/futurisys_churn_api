"""
But du fichier
--------------
Vérifier que l'endpoint `/predict` :
1) fonctionne lorsque la base SQLite temporaire (fixture `client_with_db`) est active,
2) persiste bien les **entrées** et **sorties** en base,
3) renvoie dans la réponse les identifiants `input_id` et `prediction_id`
   correspondant aux lignes créées.

Hypothèses / prérequis
----------------------
- La fixture `client_with_db` :
  - crée une base SQLite temporaire propre,
  - crée un utilisateur, authentifie et ajoute l'en-tête `Authorization` par défaut,
  - nettoie la base et les connexions après le test.
- La fixture `model_available` skippe le test si `churn_model.joblib`
  ou `input_features.json` est absent(e).

Remarque importante
-------------------
Ce test vérifie que `input_id == 1` et `prediction_id == 1`.
Cela repose sur le fait que la base SQLite temporaire est **neuve** pour ce test
(aucune donnée existante) grâce au setup/teardown de la fixture `client_with_db`.
"""

import pytest


@pytest.mark.usefixtures("model_available")
def test_predict_with_sqlite(client_with_db, sample_payload, model_available):
    """
    Arrange:
        - Base SQLite temporaire initialisée par la fixture `client_with_db`.
        - Utilisateur déjà authentifié (en-tête Bearer ajouté par défaut).
        - `sample_payload` est un payload valide pour `/predict`.
        - Le modèle est disponible (sinon test skip).

    Act:
        - POST `/predict` avec un JSON `sample_payload`.

    Assert:
        - Réponse HTTP 200.
        - La réponse JSON contient `prediction_id` et `input_id`.
        - Comme il s'agit de la première prédiction dans une base neuve,
          on s'attend à `prediction_id == 1` et `input_id == 1`.
    """
    # Skip explicite si le modèle n'est pas disponible (sécurité supplémentaire,
    # en plus du mark/usefixtures)
    if not model_available:
        pytest.skip("Modèle non disponible")

    # --- Act ---
    response = client_with_db.post("/predict", json=sample_payload)

    # --- Assert ---
    assert response.status_code == 200, response.text
    data = response.json()

    # Présence des identifiants de persistance
    assert "prediction_id" in data
    assert "input_id" in data

    # Comme la base est fraîche pour ce test, ce sont les premiers IDs
    assert data["prediction_id"] == 1  # première sortie
    assert data["input_id"] == 1       # première entrée
