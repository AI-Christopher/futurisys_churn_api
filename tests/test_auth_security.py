"""
Tests d’authentification et de sécurité.

Contenu :
- test_register_and_login : vérifie l’inscription, le double-inscription (400),
  et le login (OK/KO) via la vraie base (fixture client_with_db).
- test_predict_requires_token : s’assure que /predict exige un jeton (401/403).
- test_api_key_gate : contrôle la présence d’une API key (X-API-Key) lorsque
  la variable d’environnement API_KEY est définie.
"""

from fastapi.testclient import TestClient
from futurisys_churn_api.api.main import app


def test_register_and_login(client_with_db):
    """
    Parcours complet :
    1) Création d’un utilisateur (201) — si déjà présent, 400 (doublon).
    2) Vérifie que re-register renvoie 400.
    3) Login OK avec les bons identifiants.
    4) Login KO (mauvais mot de passe) => 400.
    """
    # register
    r = client_with_db.post("/auth/register", params={"email": "u1@test.com", "password": "pw"})
    assert r.status_code in (201, 400)

    # doublon attendu
    r2 = client_with_db.post("/auth/register", params={"email": "u1@test.com", "password": "pw"})
    assert r2.status_code == 400

    # login OK
    r3 = client_with_db.post("/auth/token", data={"username": "u1@test.com", "password": "pw"})
    assert r3.status_code == 200

    ok = client_with_db.post("/auth/token", data={"username": "u1@test.com", "password": "pw"})
    assert ok.status_code == 200

    # login KO
    ko = client_with_db.post("/auth/token", data={"username": "u1@test.com", "password": "bad"})
    assert ko.status_code == 400


def test_predict_requires_token():
    """
    /predict doit être protégé :
    - Sans jeton, la réponse doit être 401 (Unauthorized) ou 403 (Forbidden)
      selon la configuration du projet.
    """
    client = TestClient(app)
    r = client.post(
        "/predict",
        json={
            "age": 30,
            "revenu_mensuel": 3000,
            "nombre_experiences_precedentes": 1,
            "annees_dans_l_entreprise": 2,
            "annees_depuis_la_derniere_promotion": 1,
            "satisfaction_employee_environnement": 3,
            "note_evaluation_precedente": 3,
            "satisfaction_employee_nature_travail": 4,
            "satisfaction_employee_equipe": 3,
            "satisfaction_employee_equilibre_pro_perso": 3,
            "augementation_salaire_precedente": 5,
            "nombre_participation_pee": 1,
            "nb_formations_suivies": 2,
            "distance_domicile_travail": 10,
            "niveau_education": 4,
            "genre": "F",
            "frequence_deplacement": "Frequent",
            "poste": "Manager",
            "statut_marital": "Marié(e)",
            "departement": "Consulting",
            "domaine_etude": "Transformation Digitale",
            "heure_supplementaires": "Oui",
        },
    )
    assert r.status_code in (401, 403)


def test_api_key_gate(client_no_db, sample_payload, monkeypatch):
    """
    Comportement de la clé API :
    - Si API_KEY est définie dans l’environnement, l’endpoint /predict doit
      renvoyer 401 sans en-tête X-API-Key.
    - Avec le bon X-API-Key, la requête doit passer (200).
    """
    # 1) Activer la clé côté env
    monkeypatch.setenv("API_KEY", "secret123")

    # 2) Sans X-API-Key => refusé
    r1 = client_no_db.post("/predict", json=sample_payload)
    assert r1.status_code == 401

    # 3) Avec la bonne clé => OK
    client_no_db.headers["X-API-Key"] = "secret123"
    r2 = client_no_db.post("/predict", json=sample_payload)
    assert r2.status_code == 200

    # Nettoyage du header
    client_no_db.headers.pop("X-API-Key", None)
