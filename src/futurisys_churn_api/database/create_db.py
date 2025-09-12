"""
create_db.py — Outil CLI pour créer la base PostgreSQL et (re)créer les tables.

Fonctions principales
---------------------
- ensure_database_exists() : vérifie l'existence de la BDD cible ; la crée si besoin.
- manage_database_tables() : crée les tables SQLAlchemy (avec option --recreate pour drop+create).

Usage
-----
python -m futurisys_churn_api.database.create_db
python -m futurisys_churn_api.database.create_db --recreate

Notes
-----
- Ce script se connecte d'abord à la base "postgres" (SERVER_URL) pour créer la BDD cible si nécessaire,
  puis se connecte à la BDD cible (FULL_DATABASE_URL) pour créer les tables.
- Les identifiants peuvent être fournis par variables d’environnement (recommandé), sinon les valeurs
  par défaut ci-dessous sont utilisées.

Variables d'environnement supportées
------------------------------------
DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
"""

import argparse
import os
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from futurisys_churn_api.database.connection import Base
from futurisys_churn_api.database import models  # noqa: F401 (side effect: charge les modèles)


# --- Configuration de la connexion ---
# 🔐 Bonnes pratiques : permettre d’overrider via l’environnement, sinon utiliser des valeurs par défaut.
DB_NAME = os.getenv("DB_NAME", "futurisys_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Azerty1234")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# URL pour la BDD cible et pour le serveur (base 'postgres' par défaut)
FULL_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SERVER_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"


def ensure_database_exists() -> Optional[Engine]:
    """
    Vérifie si la base `DB_NAME` est joignable. Si oui, renvoie un Engine connecté à la BDD cible.
    Sinon, tente de la créer en se connectant d'abord au serveur (base 'postgres').

    Returns
    -------
    Optional[Engine]
        Un Engine SQLAlchemy connecté à la base cible, ou None en cas d’échec.
    """
    try:
        engine = create_engine(FULL_DATABASE_URL)
        # Test de connexion/fermeture immédiate : si échec -> except
        with engine.connect() as _:
            pass
        print(f"[OK] La base '{DB_NAME}' existe déjà.")
        return engine
    except OperationalError:
        print(f"[i] La base '{DB_NAME}' n'existe pas. Tentative de création...")
        try:
            server_engine = create_engine(SERVER_URL, isolation_level="AUTOCOMMIT")
            with server_engine.connect() as connection:
                # ⚠️ DB_NAME vient d’un env/constante interne -> pas d’input utilisateur direct
                connection.execute(text(f"CREATE DATABASE {DB_NAME}"))
            print(f"[OK] Base '{DB_NAME}' créée.")
            return create_engine(FULL_DATABASE_URL)
        except Exception as e:
            print(f"[ERREUR] Impossible de créer la base '{DB_NAME}': {e}")
            return None


def manage_database_tables(engine: Engine, recreate: bool = False) -> None:
    """
    Crée les tables SQLAlchemy (à partir de Base.metadata). Si `recreate=True`, supprime d'abord.

    Parameters
    ----------
    engine : Engine
        Engine SQLAlchemy pointant vers la base cible (FULL_DATABASE_URL).
    recreate : bool, default False
        Si True, fait un drop_all() avant create_all().

    Returns
    -------
    None
    """
    # S’assure que les modèles sont importés (side effect de l’import plus haut).
    _ = models  # noqa: F841

    if recreate:
        print("[!] Suppression des tables existantes (drop_all)...")
        try:
            Base.metadata.drop_all(bind=engine)
            print("[OK] Tables supprimées.")
        except Exception as e:
            print(f"[ERREUR] Drop tables: {e}")
            return

    print("[i] Création des tables (create_all)...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Tables créées.")
    except Exception as e:
        print(f"[ERREUR] Create tables: {e}")


def main() -> None:
    """Point d’entrée CLI."""
    parser = argparse.ArgumentParser(description="Gère la BDD et les tables pour Futurisys.")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Supprime les tables existantes avant de les recréer.",
    )
    args = parser.parse_args()

    # Étape 1 : s’assurer que la base existe et récupérer l’engine
    db_engine = ensure_database_exists()

    # Étape 2 : créer (ou recréer) les tables si la connexion est OK
    if db_engine:
        manage_database_tables(engine=db_engine, recreate=args.recreate)
    else:
        print("[x] Abandon : connexion à la base échouée.")


if __name__ == "__main__":
    main()
