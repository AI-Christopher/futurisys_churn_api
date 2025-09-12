"""
seed_db.py — Remplit la base avec des entrées de prédiction à partir d'un CSV.

Ce script :
1) s'assure qu'un utilisateur "system" existe (création si besoin),
2) vide les tables de prédiction,
3) charge un CSV,
4) insère les lignes comme `PredictionInput`, en les rattachant au user "system".

L’utilisation est pensée pour un environnement LOCAL (BASE ACTIVÉE).
En production (ex: Hugging Face Spaces), la base est généralement désactivée.
"""
import os
from pathlib import Path
from typing import Optional, List

import pandas as pd
from sqlalchemy.orm import sessionmaker, Session

from futurisys_churn_api.database.connection import engine
from futurisys_churn_api.database.models import PredictionInput, PredictionOutput, User
from futurisys_churn_api.api.security import get_password_hash

# --- CONFIG ---
# Chemin CSV — surcharge possible par une variable d'env.
DATASET_PATH = Path(os.getenv("DATASET_PATH", "data/data_employees.csv"))

# Fabrique de session (uniquement si la BDD est active et `engine` non-null)
SessionLocal: Optional[sessionmaker] = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
)


def require_db() -> None:
    """Valide que la base est bien active/configurée (engine et SessionLocal disponibles)."""
    if engine is None or SessionLocal is None:
        raise RuntimeError(
            "La base de données n'est pas activée ou la connexion a échoué.\n"
            "• Vérifie les variables d'env: DATABASE_ENABLED=true et DATABASE_URL\n"
            "• Exécute d'abord la création/connexion (create_db) si nécessaire."
        )


def get_or_create_system_user(db: Session) -> User:
    """
    Retourne un utilisateur 'system@futurisys.com' ; le crée s'il n'existe pas.
    Cet utilisateur sert uniquement d'identifiant technique pour les seeds.
    """
    user = db.query(User).filter(User.email == "system@futurisys.com").first()
    if user:
        return user

    print("Utilisateur 'system' non trouvé. Création…")
    user = User(
        email="system@futurisys.com",
        hashed_password=get_password_hash("system_password"),  # mot de passe factice
        role="admin",
        is_active=False,  # désactivé (sécurité)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Utilisateur 'system' créé avec l'ID: {user.id}")
    return user


def load_dataset(path: Path) -> pd.DataFrame:
    """Charge le CSV et lève une erreur explicite si le fichier est absent."""
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset introuvable: {path}. "
            "Ajuste DATASET_PATH ou place le fichier au bon endroit."
        )
    print(f"Lecture du dataset: {path}")
    return pd.read_csv(path)


def compute_input_columns() -> List[str]:
    """
    Calcule les colonnes de PredictionInput à remplir depuis le CSV.
    Exclut les colonnes auto-gérées par la DB (id/timestamp).
    """
    return [c.name for c in PredictionInput.__table__.columns if c.name not in ("id", "timestamp")]


def seed_database() -> None:
    """Pipeline de seed principal : purge, chargement CSV, insertion en masse."""
    require_db()
    assert SessionLocal is not None  # pour les hints

    with SessionLocal() as db:
        try:
            # 1) Assurer l’existence du user technique
            system_user = get_or_create_system_user(db)

            # 2) Purger les tables de prédiction (outputs puis inputs)
            print("Nettoyage des tables de prédiction…")
            db.query(PredictionOutput).delete()
            db.query(PredictionInput).delete()
            db.commit()
            print("Tables nettoyées.")

            # 3) Charger le CSV
            df = load_dataset(DATASET_PATH)

            # 4) Préparer les colonnes attendues par PredictionInput
            expected_cols = compute_input_columns()
            # On ne va pas remplir ces colonnes depuis le CSV :
            #   - id/timestamp sont auto-gérées
            #   - user_id est ajouté ci-dessous (pour rattacher au user 'system')
            # expected_cols contient déjà user_id et toutes les features d'entrée
            if "user_id" in expected_cols:
                df["user_id"] = system_user.id

            # Restriction + ordre des colonnes selon le modèle SQLAlchemy
            missing = [c for c in expected_cols if c not in df.columns]
            if missing:
                raise ValueError(
                    "Le CSV ne contient pas toutes les colonnes attendues par PredictionInput.\n"
                    f"Colonnes manquantes: {missing}\n"
                    f"Colonnes CSV: {list(df.columns)}"
                )

            df_to_insert = df[expected_cols]

            # 5) Insertion en masse
            rows = df_to_insert.to_dict(orient="records")
            print(f"{len(rows)} lignes prêtes à être insérées…")
            if rows:
                db.bulk_insert_mappings(PredictionInput, rows)
                db.commit()
            print("Données insérées avec succès.")

        except Exception as e:
            db.rollback()
            print(f"[ERREUR] {e}")
            raise
        finally:
            # Le `with SessionLocal()` gère la fermeture, mais on peut logguer :
            print("Seed terminé.")


if __name__ == "__main__":
    seed_database()