"""
Modèles ORM (SQLAlchemy) pour la traçabilité des prédictions.

Tables
------
- users               : comptes API (authentification / rôles)
- prediction_inputs   : toutes les données d'entrée envoyées au modèle
- prediction_outputs  : résultat du modèle pour une entrée donnée

Relations (simplifiées)
-----------------------
- prediction_inputs.user_id  -> users.id           (plusieurs inputs peuvent appartenir à un même user)
- prediction_outputs.input_id -> prediction_inputs.id  (1–1 : une sortie par entrée)
- prediction_outputs.user_id  -> users.id          (qui a lancé la prédiction)
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .connection import Base

class PredictionInput(Base):
    """
    Entrée brute d'une requête de prédiction (payload utilisateur).

    Cette table stocke **toutes** les colonnes reçues par l’API (/predict) afin
    d'assurer une traçabilité complète : qui a demandé quoi, et quand.
    """
    __tablename__ = "prediction_inputs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    age = Column(Integer)
    revenu_mensuel = Column(Integer)
    nombre_experiences_precedentes = Column(Integer)
    annees_dans_l_entreprise = Column(Integer)
    annees_depuis_la_derniere_promotion = Column(Integer)
    satisfaction_employee_environnement = Column(Integer)
    note_evaluation_precedente = Column(Integer)
    satisfaction_employee_nature_travail = Column(Integer)
    satisfaction_employee_equipe = Column(Integer)
    satisfaction_employee_equilibre_pro_perso = Column(Integer)
    augementation_salaire_precedente = Column(Integer)
    nombre_participation_pee = Column(Integer)
    nb_formations_suivies = Column(Integer)
    distance_domicile_travail = Column(Integer)
    niveau_education = Column(Integer)
    genre = Column(String)
    frequence_deplacement = Column(String)
    poste = Column(String)
    statut_marital = Column(String)
    departement = Column(String)
    domaine_etude = Column(String)
    heure_supplementaires = Column(String)

    # Relations
    # 1–1 : une sortie (PredictionOutput) pour une entrée
    output = relationship("PredictionOutput", back_populates="input", uselist=False)
    # Référence vers l’utilisateur (pas de back_populates ici pour rester minimal)
    user = relationship("User")

class User(Base):
    """
    Utilisateur applicatif (authentification & autorisation).

    Champs:
    - email (unique)           : identifiant de connexion (utilisé comme 'username')
    - hashed_password          : mot de passe haché (bcrypt via passlib)
    - role                     : 'viewer' | 'analyst' | 'admin'
    - is_active                : compte actif / désactivé
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="viewer")  # ex: viewer, analyst, admin
    is_active = Column(Boolean, default=True)

    # Toutes les sorties liées à cet utilisateur
    predictions = relationship("PredictionOutput", back_populates="user")

class PredictionOutput(Base):
    """
    Sortie du modèle pour une entrée donnée.

    Contient la prédiction binaire (0/1) et la probabilité associée.
    """
    __tablename__ = "prediction_outputs"

    id = Column(Integer, primary_key=True, index=True)
    input_id = Column(Integer, ForeignKey("prediction_inputs.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    prediction = Column(Integer)
    churn_probability = Column(Float)
    
    # Relation inverse
    input = relationship("PredictionInput", back_populates="output")
    user = relationship("User", back_populates="predictions")

