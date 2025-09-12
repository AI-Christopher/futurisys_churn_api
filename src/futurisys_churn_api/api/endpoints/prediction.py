"""
Endpoint de prédiction du churn (probabilité de démission).

Fonctionnement (vue d'ensemble)
-------------------------------
1) Valide et reçoit un payload conforme à `EmployeeData` (Pydantic).
2) Prépare les données (binarisation, features dérivées, encodage).
3) Aligne les colonnes avec celles attendues par le modèle (input_features.json).
4) Appelle le modèle (joblib) pour obtenir:
   - `prediction` : 0 (reste) ou 1 (part)
   - `churn_probability` : probabilité associée (0.0–1.0)
5) Si une base de données est active, enregistre l'entrée/sortie.
6) Retourne la réponse JSON (et ajoute les ids si DB active).

Sécurité
--------
- JWT obligatoire (scope `predict:read`) via `get_current_user`.
- Clé d'API optionnelle via `verify_api_key` :
  - si la variable d'env `API_KEY` est **définie** → la requête doit inclure `X-API-Key: <valeur>`.
  - sinon → aucun contrôle par clé d'API.

Notes
-----
- Le chargement du modèle et des features se fait au démarrage du module.
- Les tests couvrent le mode avec BDD et sans BDD.
"""
import json
import joblib
from typing import Generator, Optional, Dict, Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Depends, Security
from sqlalchemy.orm import Session

from ..preprocessing import convert_binary_to_int, add_features, encode_categorical
from ..schemas import EmployeeData
from ..security import get_current_user, verify_api_key
from ...database.connection import SessionLocal
from ...database import models
from ...database.models import User

# Routeur du "module" prediction
router = APIRouter()

# --- CHARGEMENT DES ARTEFACTS AU DÉMARRAGE ---
# Modèle et liste des features attendues (contrat d'interface avec le préprocessing)
model = joblib.load("models/churn_model.joblib")
with open("models/input_features.json", "r") as f:
    model_features = json.load(f)


def get_db() -> Generator[Optional[Session], None, None]:
    """
    Fournit une session SQLAlchemy si la base est activée, sinon `None`.

    Yields
    ------
    Session | None
        Une session active à utiliser dans la requête, ou None si BDD désactivée.
    """
    if SessionLocal is None:
        # Mode "sans base" (ex: Hugging Face Space) : on renvoie None.
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
    _api_key_ok = Security(verify_api_key),
    current_user: User = Security(get_current_user, scopes=["predict:read"]),
    db: Optional[Session] = Depends(get_db)
    ) -> Dict[str, Any]:
    """
    Prédit la probabilité de démission d'un employé et journalise (si DB active).

    Paramètres
    ----------
    employee_data : EmployeeData
        Données brutes validées par Pydantic.
    _api_key_ok : None
        Dépendance de sécurité (clé API). Ne renvoie rien si OK; lève 401 sinon,
        **uniquement** si la variable d'env `API_KEY` est définie.
    current_user : User
        Utilisateur authentifié (JWT) avec le scope `predict:read`.
    db : Session | None
        Session SQLAlchemy si base activée, sinon None.

    Retour
    ------
    dict
        - Sans DB : {"prediction": int, "churn_probability": float}
        - Avec DB : {"prediction_id": int, "input_id": int, "prediction": int, "churn_probability": float}

    Erreurs
    -------
    400 : problème de typage/convertibilité des features
    500 : erreur lors de la prédiction ou lors de l'écriture en base
    """
    # 1) DataFrame à une ligne à partir du payload validé
    input_df = pd.DataFrame([employee_data.model_dump()])

    # 2) Préprocessing
    # 2.1 binarisation de colonnes (Oui/Non, F/M => 1/0)
    input_df = convert_binary_to_int(input_df, 'heure_supplementaires', positive_value='Oui')
    input_df = convert_binary_to_int(input_df, 'genre', positive_value='F')

    # 2.2 création de features dérivées
    input_df = add_features(input_df)

    # 2.3 encodage catégoriel (one-hot + mapping ordinal)
    input_df = encode_categorical(input_df)

    # 2.4 alignement des colonnes avec le contrat du modèle
    final_df = input_df.reindex(columns=model_features, fill_value=0)

    # 2.5 cast en float (certaines libs de ML exigent des numériques purs)
    try:
        final_df = final_df.astype(float)
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Erreur de conversion de type des données : {e}"
        )

    # 3) Prédiction
    try:
        prediction = model.predict(final_df)
        probability = model.predict_proba(final_df)
        churn_probability = probability[0][1]
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la prédiction : {e}"
        )

    # 4) Persistance si DB active
    if db:
        try:
            # Entrée (brute) + rattachement utilisateur
            input_data_dict = employee_data.model_dump()
            if current_user:
                input_data_dict['user_id'] = current_user.id
            
            db_input = models.PredictionInput(**input_data_dict)
            db.add(db_input)
            db.flush()  # récupère db_input.id sans commit total

            # Sortie (résultat du modèle)
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
                "input_id": db_input.id,
                "prediction": int(prediction[0]),
                "churn_probability": float(churn_probability),
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, 
                detail=f"Erreur de base de données : {e}"
            )
    else:
        # 5) Mode sans base : on répond simplement le résultat
        return {
            "prediction": int(prediction[0]),
            "churn_probability": float(churn_probability),
        }