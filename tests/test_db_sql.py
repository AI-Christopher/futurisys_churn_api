# tests/test_db_sql.py
import os
import importlib
import pathlib
from sqlalchemy import inspect
from sqlalchemy.orm import close_all_sessions
from fastapi.testclient import TestClient
import pytest

@pytest.mark.usefixtures("model_available")
def test_predict_with_sqlite(sample_payload, model_available):
    if not model_available:
        pytest.skip("Modèle non disponible")

    # DB SQLite fichier avec chemin ABSOLU
    db_file = (pathlib.Path.cwd() / "tests" / "_tmp_api.db")
    if db_file.exists():
        db_file.unlink()
    os.environ["DATABASE_ENABLED"] = "true"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file.as_posix()}"

    # 1) Recharger la couche DB pour prendre en compte les env
    from futurisys_churn_api.database import connection as conn
    importlib.reload(conn)

    # 2) Importer les modèles (peuple Base)
    from futurisys_churn_api.database import models

    # 3) Créer les tables sur le même engine
    models.Base.metadata.create_all(bind=conn.engine)

    # Sanity check
    insp = inspect(conn.engine)
    assert "prediction_inputs" in insp.get_table_names()
    assert "prediction_outputs" in insp.get_table_names()

    # 4) Recharger l’endpoint (utilisera le SessionLocal de connection)
    from futurisys_churn_api.api.endpoints import prediction as pred_mod
    importlib.reload(pred_mod)

    # 5) Override de la dépendance DB pour être sûr d'utiliser le même SessionLocal
    from futurisys_churn_api.api.main import app
    def _override_get_db():
        db = conn.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[pred_mod.get_db] = _override_get_db

    # 6) Test client en contexte -> fermeture propre à la sortie
    with TestClient(app) as client:
        r = client.post("/predict", json=sample_payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "prediction_id" in data and "input_id" in data

    # 7) Vérif en base
    db = conn.SessionLocal()
    try:
        from futurisys_churn_api.database.models import PredictionInput, PredictionOutput
        assert db.query(PredictionInput).count() == 1
        assert db.query(PredictionOutput).count() == 1
    finally:
        db.close()

    # 8) Nettoyage : retire l’override, ferme sessions, libère l’engine, puis supprime le fichier
    app.dependency_overrides.clear()
    close_all_sessions()
    if conn.engine is not None:
        conn.engine.dispose()

    if db_file.exists():
        db_file.unlink()
