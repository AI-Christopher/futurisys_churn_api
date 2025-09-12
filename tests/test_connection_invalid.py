"""
But du test
-----------
Valider le comportement de repli ("fallback") de la couche de connexion
lorsqu'une URL de base de données invalide est fournie.

Contexte
--------
- Le module `futurisys_churn_api.database.connection` initialise `engine`
  et `SessionLocal` au moment de l'import, en fonction des variables
  d'environnement `DATABASE_ENABLED` et `DATABASE_URL`.
- En cas d'échec de connexion (URL invalide, driver manquant, etc.),
  le module remet explicitement `engine = None` et `SessionLocal = None`
  pour permettre à l'API de continuer à tourner sans BDD.

Ce test force une URL invalide, recharge le module, puis vérifie que
`engine` et `SessionLocal` sont bien `None`.
"""

import importlib


def test_connection_invalid_url_triggers_fallback(monkeypatch):
    """
    Arrange:
        - Active la BDD via `DATABASE_ENABLED=true`
        - Fournit une URL volontairement invalide (`invaliddb://whatever`)
    Act:
        - Recharge le module `connection` pour relancer l'init avec ces env
    Assert:
        - `engine` et `SessionLocal` doivent être `None` (fallback OK)
    """
    # On passe par monkeypatch pour éviter de "polluer" l'env global du process
    monkeypatch.setenv("DATABASE_ENABLED", "true")
    monkeypatch.setenv("DATABASE_URL", "invaliddb://whatever")  # force une erreur immédiate

    # Important : recharger le module pour réexécuter sa logique d'initialisation
    from futurisys_churn_api.database import connection as conn
    importlib.reload(conn)

    # Fallback attendu : pas d'engine ni de fabrique de sessions
    assert conn.engine is None
    assert conn.SessionLocal is None

