import pandas as pd
from sqlalchemy.orm import sessionmaker
from futurisys_churn_api.database.connection import engine
from futurisys_churn_api.database.models import PredictionInput, PredictionOutput, User
from futurisys_churn_api.api.security import get_password_hash

# --- Configuration ---
# Chemin vers dataset CSV.
# On suppose que le script est lancé depuis la racine du projet.
DATASET_PATH = "data/data_employees.csv"

# Crée une session pour interagir avec la base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = SessionLocal()

def get_or_create_system_user():
    """
    Vérifie si un utilisateur 'system' existe, sinon le crée.
    Retourne l'objet utilisateur.
    """
    system_user = db_session.query(User).filter(User.email == "system@futurisys.com").first()
    
    if not system_user:
        print("Utilisateur 'system' non trouvé. Création...")
        # On utilise un mot de passe factice car cet utilisateur ne se connectera jamais
        hashed_password = get_password_hash("system_password")
        system_user = User(
            email="system@futurisys.com",
            hashed_password=hashed_password,
            role="admin", # On lui donne un rôle admin
            is_active=False # On peut le désactiver pour plus de sécurité
        )
        db_session.add(system_user)
        db_session.commit()
        db_session.refresh(system_user)
        print(f"Utilisateur 'system' créé avec l'ID : {system_user.id}")
    
    return system_user

def seed_database():
    """
    Vide les tables de prédiction et les remplit avec les données du dataset CSV.
    """
    try:
        # --- Étape 1: Créer l'utilisateur système ---
        system_user = get_or_create_system_user()

        # --- Étape 2: Nettoyer les tables ---
        print("Nettoyage des tables de prédiction...")
        db_session.query(PredictionOutput).delete()
        db_session.query(PredictionInput).delete()
        db_session.commit()
        print("Tables nettoyées.")

        # --- Étape 3: Lire et préparer le dataset ---
        print(f"Lecture du dataset depuis : {DATASET_PATH}")
        df = pd.read_csv(DATASET_PATH)

        # Ajoute la colonne user_id à chaque ligne du DataFrame
        df['user_id'] = system_user.id
        print(f"Assignation de toutes les entrées à l'utilisateur ID : {system_user.id}")
        
        # S'assurer que le DataFrame ne contient que les colonnes attendues par la table
        input_columns = [c.name for c in PredictionInput.__table__.columns if c.name not in ['id', 'timestamp']]
        df_to_insert = df[input_columns]

        # Convertit le DataFrame en une liste de dictionnaires
        data_to_insert = df_to_insert.to_dict(orient='records')
        print(f"{len(data_to_insert)} lignes prêtes à être insérées.")

        # --- Étape 4: Insérer les nouvelles données ---
        print("Insertion des données du dataset...")
        db_session.bulk_insert_mappings(PredictionInput, data_to_insert)
        db_session.commit()
        print("Données insérées avec succès.")

    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == "__main__":
    seed_database()