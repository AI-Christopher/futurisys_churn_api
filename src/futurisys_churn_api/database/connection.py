"""
Gestion de la connexion base de données (SQLAlchemy).

Principe
--------
- En prod (Hugging Face Spaces) on utilise généralement l'API **sans** base :
  `DATABASE_ENABLED=false` -> aucune tentative de connexion.
- En local / CI, on peut activer la persistance :
  `DATABASE_ENABLED=true` + `DATABASE_URL` (sqlite:///..., postgresql://...).

Sécurité & Robustesse
---------------------
- Pas d'URL par défaut avec mot de passe en dur : on lit l'ENV à l'exécution.
- Si la connexion échoue, on remet `engine` et `SessionLocal` à `None` pour
  laisser l'API fonctionner en mode "sans DB".
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Lecture des variables d'environnement ---
DATABASE_ENABLED = os.environ.get("DATABASE_ENABLED", "false").lower() == "true"
# Pas de fallback ici : si non défini, on n'essaie pas de se connecter
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:Azerty1234@localhost:5432/futurisys_db")

# Objets de connexion (peuvent rester à None si DB désactivée/indisponible)
engine = None
SessionLocal = None

if DATABASE_ENABLED:
    try:
        # Options spécifiques SQLite (threading)
        connect_args = {}
        if DATABASE_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        
        # Engine + fabrique de sessions
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        print("Connexion à la base de données établie avec succès.")
    except Exception as e:
        # Si la connexion échoue, on retombe en mode "sans DB"
        print(f"ATTENTION: Erreur de connexion à la base de données : {e}")
        engine = None
        SessionLocal = None
else:
    # Mode "sans DB" (par défaut en prod/HF)
    print("Connexion à la base de données désactivée.")

# Base ORM (déclarative)
Base = declarative_base()