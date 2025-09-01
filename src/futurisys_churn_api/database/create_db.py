from futurisys_churn_api.database.connection import engine, Base
# On importe les modèles pour qu'ils soient "connus" de Base
from futurisys_churn_api.database import models

def create_database_tables():
    print("Création des tables dans la base de données...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables créées avec succès.")
    except Exception as e:
        print(f"Erreur lors de la création des tables : {e}")

if __name__ == "__main__":
    create_database_tables()