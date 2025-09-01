import joblib
import json
import re
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from ..schemas import EmployeeData
from ...database.connection import SessionLocal
from ...database import models
from sqlalchemy.orm import Session

# Crée un "routeur". C'est comme un mini-chapitre de notre API
router = APIRouter()

# --- CHARGEMENT DES ARTEFACTS AU DÉMARRAGE ---
# On charge le modèle et la liste des features attendues
model = joblib.load("models/churn_model.joblib")
with open("models/input_features.json", "r") as f:
    model_features = json.load(f)

def clean_col_names(df):
    cols = df.columns
    new_cols = []
    for col in cols:
        new_col = re.sub(r'[^A-Za-z0-9_]+', '', col)
        new_cols.append(new_col)
    df.columns = new_cols
    return df


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
def predict_churn(employee_data: EmployeeData, db: Session = Depends(get_db)):
    """
    Prédit la probabilité de démission d'un employé.
    """

    # 1. Enregistrer les données d'entrée dans la base
    #db_input = models.PredictionInput(**employee_data.model_dump())
    #db.add(db_input)
    #db.commit()
    #db.refresh(db_input) # Pour récupérer l'ID auto-généré

    # 2. Convertir les données d'entrée en DataFrame
    input_df = pd.DataFrame([employee_data.model_dump()])

    # 3.--- DÉBUT DU PREPROCESSING DANS L'API ---
    # Binarisation (recrée tes fonctions ou applique la logique directement)
    input_df['heure_supplementaires'] = (input_df['heure_supplementaires'] == 'Oui').astype(int)
    input_df['genre'] = (input_df['genre'] == 'F').astype(int)
    #Création de features (Feature Engineering)
    # Revenue par rapport à la moyenne du poste
    # On calcule le revenu moyen par poste et on le compare au revenu de l'employé.
    moyennes_poste = {
        "Représentant Commercial": 2626.0,
        "Consultant": 3237.17,
        "Assistant de Direction": 3239.97,
        "Ressources Humaines": 4235.75,
        "Cadre Commercial": 6924.28,
        "Tech Lead": 7295.14,
        "Manager": 7528.76,
        "Directeur Technique": 16033.55,
        "Senior Manager": 17181.67
    }
    # La méthode .map() va chercher la moyenne correspondante dans le dictionnaire
    revenu_moyen_par_poste = input_df['poste'].map(moyennes_poste)
    # On calcule le ratio en utilisant cette moyenne
    input_df['ratio_revenu_poste'] = input_df['revenu_mensuel'] / (revenu_moyen_par_poste + 1)
    
    # Gérer le cas où un poste inconnu serait envoyé (map retournerait NaN)
    # Dans ce cas, on peut utiliser une moyenne globale ou mettre 1 par défaut.
    input_df['ratio_revenu_poste'].fillna(1, inplace=True) 
    
    # Ratio Augmentation / Promotion
    # On met en relation l'augmentation de salaire avec le temps écoulé depuis la dernière promotion.
    input_df['ratio_augmentation_promotion'] = input_df['augementation_salaire_precedente'] / (input_df['annees_depuis_la_derniere_promotion'] + 1)
    
    # Encodage des variables catégorielles (One-Hot Encoding)
    categorical_cols_to_encode = ['statut_marital', 'domaine_etude', 'departement']
    input_df = pd.get_dummies(input_df, columns=categorical_cols_to_encode, dummy_na=False)
    input_df = clean_col_names(input_df)
    # Encodage Ordinal
    mapping_poste = {'Représentant Commercial': 0, 'Consultant': 1, 'Assistant de Direction': 2, 'Ressources Humaines': 3, 'Cadre Commercial': 4, 'Tech Lead': 5, 'Manager': 6, 'Directeur Technique': 7, 'Senior Manager': 8}
    input_df['poste'] = input_df['poste'].map(mapping_poste)

    mapping_freq_dict = {'Aucun': 0, 'Occasionnel': 1, 'Fréquent': 2}
    input_df['frequence_deplacement'] = input_df['frequence_deplacement'].map(mapping_freq_dict)

    # Alignement final des colonnes
    final_df = pd.DataFrame(columns=model_features)
    final_df = pd.concat([final_df, input_df])
    final_df.fillna(0, inplace=True) # Remplit les colonnes manquantes (dummies) avec 0
    final_df = final_df[model_features] # Assure le bon ordre et supprime les colonnes en trop

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
    if db: # On vérifie si une session de BDD a été fournie
        print("Enregistrement dans la base de données...")
        db_input = models.PredictionInput(**employee_data.model_dump())
        db.add(db_input)
        db.commit()
        db.refresh(db_input)
        
        db_output = models.PredictionOutput(
            input_id=db_input.id,
            prediction=int(prediction[0]),
            churn_probability=float(churn_probability)
        )
        db.add(db_output)
        db.commit()
        db.refresh(db_output)

        # Retourner la réponse avec les IDs
        return {
            "prediction_id": db_output.id,
            "input_id": db_input.id,
            "prediction": int(prediction[0]),
            "churn_probability": float(churn_probability)
        }
    else:
        # Si pas de BDD, on retourne juste la prédiction
        print("Pas de base de données configurée, on retourne la prédiction seule.")
        return {
            "prediction": int(prediction[0]),
            "churn_probability": float(churn_probability)
        }