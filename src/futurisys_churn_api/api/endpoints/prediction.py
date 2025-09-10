import joblib
import json
import pandas as pd
from ..preprocessing import convert_binary_to_int, add_features, encode_categorical
from fastapi import APIRouter, HTTPException, Depends, Security
from ..security import get_current_user, verify_api_key
from ..schemas import EmployeeData
from ...database.connection import SessionLocal
from ...database import models
from ...database.models import User
from sqlalchemy.orm import Session

# Crée un "routeur". C'est comme un mini-chapitre de notre API
router = APIRouter()

# --- CHARGEMENT DES ARTEFACTS AU DÉMARRAGE ---
# On charge le modèle et la liste des features attendues
model = joblib.load("models/churn_model.joblib")
with open("models/input_features.json", "r") as f:
    model_features = json.load(f)

# Fonction pour obtenir une session de base de données
def get_db():
    # Si SessionLocal n'a pas pu être créé, on ne fait rien
    if SessionLocal is None:
        yield None
        return
        
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/predict", tags=["Predictions"])
def predict_churn(
    employee_data: EmployeeData,
    _api_key_ok = Security(verify_api_key, use_cache=False), # use_cache=False est une bonne pratique
    current_user: User = Security(get_current_user, scopes=["predict:read"], use_cache=False),
    db: Session = Depends(get_db)
                  ):
    """
    Prédit la probabilité de démission d'un employé.
    """
    # 1. Convertir les données d'entrée en DataFrame
    input_df = pd.DataFrame([employee_data.model_dump()])

    # 2.--- DÉBUT DU PREPROCESSING DANS L'API ---
    # --- BINARISATION ---
    input_df = convert_binary_to_int(input_df, 'heure_supplementaires', positive_value='Oui')
    input_df = convert_binary_to_int(input_df, 'genre', positive_value='F')

    # --- CRÉATION DE FEATURES (Feature Engineering) ---
    input_df = add_features(input_df)

    # --- ENCODAGE ---
    input_df = encode_categorical(input_df)

    # Alignement final des colonnes
    #final_df = pd.DataFrame(columns=model_features)
    #final_df = pd.concat([final_df, input_df])
    #final_df.fillna(0, inplace=True) # Remplit les colonnes manquantes (dummies) avec 0
    #final_df = final_df[model_features] # Assure le bon ordre et supprime les colonnes en trop
    final_df = input_df.reindex(columns=model_features, fill_value=0)

    try:
        final_df = final_df.astype(float)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur de conversion de type des données : {e}")

    # --- FIN DU PREPROCESSING ---

    # 4. Prédiction
    try:
        prediction = model.predict(final_df)
        probability = model.predict_proba(final_df)
        churn_probability = probability[0][1]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction : {e}")
    
    # 5. Enregistrer les résultats dans la base
    if db:
        try:
            # On crée le dictionnaire complet pour l'input
            input_data_dict = employee_data.model_dump()
            if current_user:
                input_data_dict['user_id'] = current_user.id
            
            db_input = models.PredictionInput(**input_data_dict)
            db.add(db_input)
            db.flush() # Récupère l'ID de l'input

            db_output = models.PredictionOutput(
                input_id=db_input.id,
                user_id=current_user.id if current_user else None,
                prediction=int(prediction[0]),
                churn_probability=float(churn_probability),
            )
            db.add(db_output)
            db.commit()
            db.refresh(db_output)
            
            return {
                "prediction_id": db_output.id,
                "prediction": int(prediction[0]),
                "churn_probability": float(churn_probability),
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Erreur de base de données : {e}")
    else:
        # Mode sans BDD
        return {
            "prediction": int(prediction[0]),
            "churn_probability": float(churn_probability),
        }
