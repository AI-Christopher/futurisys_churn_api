import os
import importlib

def test_connection_invalid_url_triggers_fallback(monkeypatch):
    os.environ["DATABASE_ENABLED"] = "true"
    os.environ["DATABASE_URL"] = "invaliddb://whatever"  # force une erreur immédiate

    from futurisys_churn_api.database import connection as conn
    importlib.reload(conn)

    assert conn.engine is None
    assert conn.SessionLocal is None
