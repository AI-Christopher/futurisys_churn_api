"""
batch_predict.py — Génère des prédictions en lot pour les entrées sans sortie.

Ce script :
1) récupère dans la base toutes les lignes de `prediction_inputs` qui n'ont PAS encore
   de `prediction_outputs` associée ;
2) applique **le même preprocessing** que l'endpoint /predict ;
3) appelle le modèle pour produire `prediction` + `churn_probability` ;
4) écrit les résultats dans `prediction_outputs`.

Usage (local, avec BDD activée) :
    export DATABASE_ENABLED=true
    export DATABASE_URL="postgresql://postgres:password@localhost:5432/futurisys_db"
    uv run python -m futurisys_churn_api.scripts.batch_predict
"""

import sys
import json
from typing import List, Sequence

import joblib
import pandas as pd
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import not_

from futurisys_churn_api.database.connection import engine
from futurisys_churn_api.database.models import (
    PredictionInput,
    PredictionOutput,
)
from futurisys_churn_api.api.preprocessing import (
    convert_binary_to_int,
    add_features,
    encode_categorical,
)


# ---------- Chargement des artefacts (modèle + features) ----------

def load_artifacts():
    """
    Charge le modèle et la liste des features attendues par le modèle.
    Lève SystemExit avec message clair si un artefact est manquant.
    """
    try:
        model = joblib.load("models/churn_model.joblib")
    except FileNotFoundError:
        print("ERREUR: 'models/churn_model.joblib' introuvable.")
        sys.exit(1)

    try:
        with open("models/input_features.json", "r", encoding="utf-8") as f:
            model_features = json.load(f)
    except FileNotFoundError:
        print("ERREUR: 'models/input_features.json' introuvable.")
        sys.exit(1)

    if not isinstance(model_features, list) or not model_features:
        print("ERREUR: 'input_features.json' n'est pas une liste valide de colonnes.")
        sys.exit(1)

    return model, model_features


# ---------- Accès DB ----------

def get_session_factory() -> sessionmaker:
    """
    Retourne un sessionmaker lié à l'engine.
    Lève SystemExit si la BDD n'est pas active/configurée.
    """
    if engine is None:
        print(
            "ERREUR: Base de données désactivée ou non initialisée.\n"
            "• Assure-toi d'avoir DATABASE_ENABLED=true et DATABASE_URL définie.\n"
            "• Crée les tables si nécessaire (create_db)."
        )
        sys.exit(1)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------- Extraction des inputs ----------

def fetch_inputs_without_outputs(db: Session) -> Sequence[PredictionInput]:
    """
    Récupère toutes les entrées qui n'ont pas encore de sortie associée.
    """
    return (
        db.query(PredictionInput)
        .filter(not_(PredictionInput.output.has()))
        .all()
    )


def to_dataframe(objs: Sequence[PredictionInput]) -> pd.DataFrame:
    """
    Convertit une liste d'objets SQLAlchemy PredictionInput en DataFrame propre.
    On n'extrait que les colonnes définies dans la table (pas les attributs internes SA).
    """
    if not objs:
        return pd.DataFrame()

    cols: List[str] = [c.name for c in PredictionInput.__table__.columns]
    rows = [{c: getattr(o, c) for c in cols} for o in objs]
    return pd.DataFrame(rows)


# ---------- Preprocessing identique à l'API ----------

def preprocess_for_model(df_inputs: pd.DataFrame, model_features: List[str]) -> pd.DataFrame:
    """
    Rejoue le pipeline de preprocessing de l'API :
      - binarisation de 'heure_supplementaires' et 'genre'
      - création de features dérivées
      - encodage catégoriel
      - alignement final sur `model_features`
      - conversion en float
    """
    if df_inputs.empty:
        return df_inputs

    df_proc = df_inputs.copy()

    # Binarisation
    df_proc = convert_binary_to_int(df_proc, "heure_supplementaires", positive_value="Oui")
    df_proc = convert_binary_to_int(df_proc, "genre", positive_value="F")

    # Features dérivées (exige certaines colonnes — la fonction lèvera si manquantes)
    df_proc = add_features(df_proc)

    # Encodage (one-hot + mappings)
    df_proc = encode_categorical(df_proc)

    # Alignement final sur les features attendues par le modèle
    final_df = df_proc.reindex(columns=model_features, fill_value=0)

    # Types numériques
    try:
        final_df = final_df.astype(float)
    except Exception as e:
        raise ValueError(f"Erreur de conversion de types pour le modèle: {e}") from e

    return final_df


# ---------- Prédiction + insertion ----------

def save_outputs(db: Session,
                 inputs: Sequence[PredictionInput],
                 preds: pd.Series,
                 proba: pd.DataFrame) -> int:
    """
    Enregistre en base les sorties calculées.
    Retourne le nombre de sorties insérées.
    """
    outputs = []
    for i, inp in enumerate(inputs):
        out = PredictionOutput(
            input_id=inp.id,
            user_id=inp.user_id,
            prediction=int(preds[i]),
            churn_probability=float(proba[i][1]) if hasattr(proba, "__getitem__") else float(proba[i, 1]),
        )
        outputs.append(out)

    if outputs:
        db.bulk_save_objects(outputs)
        db.commit()
    return len(outputs)


def batch_predict() -> None:
    """
    Pipeline complet de prédiction en lot.
    """
    model, model_features = load_artifacts()
    SessionLocal = get_session_factory()

    with SessionLocal() as db:
        try:
            # 1) Récupération des inputs à traiter
            print("Recherche des entrées non traitées…")
            inputs = fetch_inputs_without_outputs(db)
            if not inputs:
                print("Aucune nouvelle entrée à traiter.")
                return
            print(f"{len(inputs)} entrées à traiter.")

            # 2) Conversion en DataFrame + preprocessing
            df_inputs = to_dataframe(inputs)
            print("Lancement du preprocessing…")
            X = preprocess_for_model(df_inputs, model_features)
            print(f"Preprocessing terminé. {X.shape[0]} lignes prêtes pour le modèle.")

            # 3) Prédictions
            print("Prédiction en cours…")
            y_pred = model.predict(X)
            y_proba = model.predict_proba(X)
            print("Prédiction terminée.")

            # 4) Insertion des sorties
            print("Insertion des prédictions…")
            n = save_outputs(db, inputs, y_pred, y_proba)
            print(f"{n} prédictions insérées avec succès.")

        except Exception as e:
            db.rollback()
            print(f"[ERREUR] {e}")
            raise
        finally:
            print("Batch terminé.")


if __name__ == "__main__":
    batch_predict()
