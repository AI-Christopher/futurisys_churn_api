import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from futurisys_churn_api.database.connection import Base
from futurisys_churn_api.database import models


# --- Configuration de la connexion ---
# On définit les variables de manière explicite et lisible
DB_NAME = "futurisys_db"
DB_USER = "postgres"
DB_PASSWORD = "Azerty1234" 
DB_HOST = "localhost"
DB_PORT = "5432"

# On reconstruit les URLs de connexion à partir des variables
# URL pour la base de données spécifique
FULL_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# URL pour le serveur PostgreSQL (on se connecte à la base 'postgres' par défaut)
SERVER_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"

def ensure_database_exists():
    """
    Vérifie si la base de données existe. Si non, la crée.
    Retourne l'engine de la base de données si la connexion est réussie, sinon None.
    """
    try:
        engine = create_engine(FULL_DATABASE_URL)
        engine.connect().close() # On fait un test de connexion simple
        print(f"La base de données '{DB_NAME}' existe déjà.")
        return engine
    except OperationalError:
        print(f"La base de données '{DB_NAME}' n'existe pas. Tentative de création...")
        try:
            server_engine = create_engine(SERVER_URL, isolation_level="AUTOCOMMIT")
            with server_engine.connect() as connection:
                connection.execute(text(f"CREATE DATABASE {DB_NAME}"))
            print(f"Base de données '{DB_NAME}' créée avec succès.")
            return create_engine(FULL_DATABASE_URL)
        except Exception as e:
            print(f"ERREUR: Impossible de créer la base de données : {e}")
            return None

def manage_database_tables(engine, recreate: bool = False):
    """
    Gère la création des tables de la base de données.
    Si recreate=True, supprime d'abord les tables existantes.
    """
    _ = models.Base # S'assure que les modèles sont chargés

    if recreate:
        print("Suppression des tables existantes...")
        try:
            Base.metadata.drop_all(bind=engine)
            print("Tables supprimées.")
        except Exception as e:
            print(f"Erreur lors de la suppression des tables : {e}")
            return

    print("Création des tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables créées.")
    except Exception as e:
        print(f"Erreur lors de la création des tables : {e}")

# --- Bloc principal simplifié ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gère la BDD et les tables pour Futurisys.")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Supprime les tables existantes avant de les recréer."
    )
    args = parser.parse_args()

    # Étape 1: On s'assure que la base existe et on récupère l'engine
    db_engine = ensure_database_exists()

    # Étape 2: Si on a bien un engine, on gère les tables
    if db_engine:
        manage_database_tables(engine=db_engine, recreate=args.recreate)
    else:
        print("Abandon du script car la connexion à la base de données a échoué.")

#def create_database_tables():
#    if engine is None:
#        print("BDD désactivée → on saute la création des tables.")
#        return
#    print("Création des tables…")
    # On utilise le nom "models" ici pour rendre l'import utile
    # Cette ligne ne change rien au fonctionnement, elle ne fait que charger les classes
#    _ = models.Base
#    Base.metadata.create_all(bind=engine)
#    print("Tables créées.")