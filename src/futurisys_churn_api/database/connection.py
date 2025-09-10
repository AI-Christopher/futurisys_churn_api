import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Par défaut: BDD désactivée (utile en prod/HF)
DATABASE_ENABLED = os.environ.get("DATABASE_ENABLED", "false").lower() == "true"
# Pas de fallback localhost ici: si non défini, on n’essaie PAS de se connecter
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:Azerty1234@localhost:5432/futurisys_db")

engine = None
SessionLocal = None

# On crée l'engine et la session SEULEMENT si on a une URL de BDD valide
# Sur Hugging Face, DATABASE_URL ne sera pas définie, donc ce bloc ne s'exécutera pas.
if DATABASE_ENABLED:
    try:
        connect_args = {}
        if DATABASE_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("Connexion à la base de données établie avec succès.")
    except Exception as e:
        print(f"ATTENTION: Erreur de connexion à la base de données : {e}")
        # On remet les variables à None pour que l'API puisse continuer sans BDD
        engine = None
        SessionLocal = None
else:
    print("Connexion à la base de données désactivée.")

Base = declarative_base()