import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# On utilise une variable pour activer la BDD. Si elle n'est pas à "true", on désactive.
DATABASE_ENABLED = os.environ.get("DATABASE_ENABLED", "true").lower() == "true"
# L'URL par défaut pour le développement LOCAL
# On lit une variable d'environnement, si elle n'existe pas, on prend la valeur locale.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:Azerty1234@localhost:5432/futurisys_db")

engine = None
SessionLocal = None

# On crée l'engine et la session SEULEMENT si on a une URL de BDD valide
# Sur Hugging Face, DATABASE_URL ne sera pas définie, donc ce bloc ne s'exécutera pas.
if DATABASE_ENABLED:
    try:
        engine = create_engine(DATABASE_URL)
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