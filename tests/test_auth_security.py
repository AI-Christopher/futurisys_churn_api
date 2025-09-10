from fastapi.testclient import TestClient
from futurisys_churn_api.api.main import app

def test_register_and_login(client_with_db):
    # register
    r = client_with_db.post("/auth/register", params={"email":"u1@test.com","password":"pw"})
    assert r.status_code in (201, 400)
    # Le doublon renvoie 400 (attendu)
    r2 = client_with_db.post("/auth/register", params={"email":"u1@test.com", "password":"pw"})
    assert r2.status_code == 400
    # Le login doit fonctionner
    r3 = client_with_db.post("/auth/token", data={"username":"u1@test.com", "password":"pw"})
    assert r3.status_code == 200
    # login ok
    ok = client_with_db.post("/auth/token", data={"username":"u1@test.com","password":"pw"})
    assert ok.status_code == 200
    # login bad
    ko = client_with_db.post("/auth/token", data={"username":"u1@test.com","password":"bad"})
    assert ko.status_code == 400

def test_predict_requires_token():
    client = TestClient(app)
    r = client.post("/predict", json={"age":30, "revenu_mensuel":3000, "nombre_experiences_precedentes":1,
                                      "annees_dans_l_entreprise":2, "annees_depuis_la_derniere_promotion":1,
                                      "satisfaction_employee_environnement":3, "note_evaluation_precedente":3,
                                      "satisfaction_employee_nature_travail":4, "satisfaction_employee_equipe":3,
                                      "satisfaction_employee_equilibre_pro_perso":3, "augementation_salaire_precedente":5,
                                      "nombre_participation_pee":1, "nb_formations_suivies":2, "distance_domicile_travail":10,
                                      "niveau_education":4, "genre":"F", "frequence_deplacement":"Frequent",
                                      "poste":"Manager","statut_marital":"Marié(e)","departement":"Consulting",
                                      "domaine_etude":"Transformation Digitale","heure_supplementaires":"Oui"})
    assert r.status_code in (401, 403)

def test_api_key_gate(client_no_db, sample_payload, monkeypatch):
    # 1) Activer l'API key et recharger les modules
    monkeypatch.setenv("API_KEY", "secret123")

    # 2) client_no_db a déjà l'en-tête Authorization (Bearer ...)
    #    On teste d'abord SANS X-API-Key => doit être refusé (401)
    r1 = client_no_db.post("/predict", json=sample_payload)
    assert r1.status_code == 401

    # 3) Puis AVEC la bonne clé => doit passer (200)
    client_no_db.headers["X-API-Key"] = "secret123"
    r2 = client_no_db.post("/predict", json=sample_payload)
    assert r2.status_code == 200

    # (facultatif) nettoyage
    client_no_db.headers.pop("X-API-Key", None)
