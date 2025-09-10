# Dans src/futurisys_churn_api/scripts/batch_predict.py
import pandas as pd
import joblib
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import not_
from futurisys_churn_api.database.connection import engine
from futurisys_churn_api.database.models import PredictionInput, PredictionOutput
# Importe tes fonctions de preprocessing depuis un fichier dédié
# (Tu devras créer ce fichier et y mettre tes fonctions)
from futurisys_churn_api.api.preprocessing import (
    convert_binary_to_int,
    add_features,
    encode_categorical
)

# --- Chargement des artefacts ---
try:
    model = joblib.load("models/churn_model.joblib")
    with open("models/input_features.json", "r") as f:
        model_features = json.load(f)
except FileNotFoundError:
    print("ERREUR: Fichiers du modèle (model ou features) non trouvés. Assurez-vous qu'ils sont dans le dossier /models.")
    exit()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def batch_predict():
    """
    Génère des prédictions pour toutes les entrées de la base de données
    qui n'ont pas encore de sortie associée.
    """
    db_session = SessionLocal()
    try:
        # --- Étape 1: Récupérer les entrées non traitées ---
        print("Recherche des entrées non traitées...")
        
        inputs_to_process = db_session.query(PredictionInput).filter(
            not_(PredictionInput.output.has())
        ).all()
        
        if not inputs_to_process:
            print("Aucune nouvelle entrée à traiter.")
            return

        print(f"{len(inputs_to_process)} entrées à traiter.")

        # Convertit les objets SQLAlchemy en DataFrame
        input_data_list = [vars(inp) for inp in inputs_to_process]
        input_df = pd.DataFrame(input_data_list)
        
        # --- Étape 2: Preprocessing complet ---
        print("Lancement du preprocessing...")
        
        # Copie pour éviter les avertissements de modification
        df_processed = input_df.copy()
        
        # Binarisation
        df_processed = convert_binary_to_int(df_processed, 'heure_supplementaires', positive_value='Oui')
        df_processed = convert_binary_to_int(df_processed, 'genre', positive_value='F')

        # Création de features (Feature Engineering)
        df_processed = add_features(df_processed)

        # Encodage
        df_processed = encode_categorical(df_processed)

        # Alignement final des colonnes (très important)
        # reindex est une excellente façon de faire ça proprement
        final_df = df_processed.reindex(columns=model_features, fill_value=0)
        
        # Conversion finale des types
        final_df = final_df.astype(float)
        
        print("Preprocessing terminé.")
        
        # --- Étape 3: Prédiction par lots ---
        print("Lancement de la prédiction...")
        predictions = model.predict(final_df)
        probabilities = model.predict_proba(final_df)
        print("Prédiction terminée.")

        # --- Étape 4: Insérer les nouvelles sorties ---
        print("Insertion des nouvelles prédictions dans la base de données...")
        
        outputs_to_insert = []
        for i, input_record in enumerate(inputs_to_process):
            output = PredictionOutput(
                input_id=input_record.id,
                user_id=input_record.user_id,
                prediction=int(predictions[i]),
                churn_probability=float(probabilities[i][1])
            )
            outputs_to_insert.append(output)

        # bulk_save_objects est efficace pour insérer de nombreuses lignes
        db_session.bulk_save_objects(outputs_to_insert)
        db_session.commit()
        
        print(f"{len(outputs_to_insert)} prédictions insérées avec succès.")

    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        db_session.rollback()
    finally:
        print("Fermeture de la session de la base de données.")
        db_session.close()

if __name__ == "__main__":
    batch_predict()
