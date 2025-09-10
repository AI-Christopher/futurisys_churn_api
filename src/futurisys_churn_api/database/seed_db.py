import pandas as pd
from sqlalchemy.orm import sessionmaker
from futurisys_churn_api.database.connection import engine
from futurisys_churn_api.database.models import PredictionInput, PredictionOutput

# --- Configuration ---
# Chemin vers dataset CSV.
# On suppose que le script est lancé depuis la racine du projet.
DATASET_PATH = "data/data_employees.csv"

# Crée une session pour interagir avec la base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = SessionLocal()

def seed_database():
    """
    Vide les tables de prédiction et les remplit avec les données du dataset CSV.
    """
    try:
        # --- Étape 1: Nettoyer les tables ---
        print("Nettoyage des tables existantes...")
        # On supprime d'abord les sorties à cause de la clé étrangère
        db_session.query(PredictionOutput).delete()
        db_session.query(PredictionInput).delete()
        db_session.commit()
        print("Tables nettoyées avec succès.")

        # --- Étape 2: Lire et préparer le dataset ---
        print(f"Lecture du dataset depuis : {DATASET_PATH}")
        try:
            df = pd.read_csv(DATASET_PATH)
        except FileNotFoundError:
            print(f"ERREUR: Le fichier dataset n'a pas été trouvé à l'emplacement '{DATASET_PATH}'.")
            return

        # On renomme les colonnes du DataFrame pour qu'elles correspondent EXACTEMENT
        # aux noms des attributs de la classe SQLAlchemy `PredictionInput`.
        # C'est une étape cruciale.
        # df.rename(columns={
        #     "nom_colonne_csv": "nom_attribut_sqlalchemy",
        #     "age": "age",
        #     "revenu_mensuel": "revenu_mensuel",
        #     # ... continue avec toutes les autres colonnes
        # }, inplace=True)
        
        # S'assurer que le DataFrame ne contient que les colonnes attendues par la table
        # Récupère les noms des colonnes de la table `PredictionInput`
        input_columns = [c.name for c in PredictionInput.__table__.columns if c.name not in ['id', 'timestamp']]
        df_to_insert = df[input_columns]

        # Convertit le DataFrame en une liste de dictionnaires
        data_to_insert = df_to_insert.to_dict(orient='records')
        print(f"{len(data_to_insert)} lignes prêtes à être insérées.")

        # --- Étape 3: Insérer les nouvelles données ---
        print("Insertion des données du dataset...")
        # `bulk_insert_mappings` est très efficace pour insérer de nombreuses lignes
        db_session.bulk_insert_mappings(PredictionInput, data_to_insert)
        db_session.commit()
        print("Données insérées avec succès.")

    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        db_session.rollback() # Annule les changements en cas d'erreur
    finally:
        db_session.close() # Ferme toujours la session

if __name__ == "__main__":
    seed_database()