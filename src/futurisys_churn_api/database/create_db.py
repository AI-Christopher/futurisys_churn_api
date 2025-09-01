from futurisys_churn_api.database.connection import engine, Base
# On importe les modèles pour qu'ils soient "connus" de Base
from futurisys_churn_api.database import models

def create_database_tables():
    if engine is None:
        print("BDD désactivée → on saute la création des tables.")
        return
    print("Création des tables…")
    # On utilise le nom "models" ici pour rendre l'import utile
    # Cette ligne ne change rien au fonctionnement, elle ne fait que charger les classes
    _ = models.Base
    Base.metadata.create_all(bind=engine)
    print("Tables créées.")