from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .connection import Base
from datetime import datetime, timezone

class PredictionInput(Base):
    __tablename__ = "prediction_inputs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    age = Column(Integer)
    revenu_mensuel = Column(Integer)
    nombre_experiences_precedentes = Column(Integer)
    annee_experience_totale = Column(Integer)
    annees_dans_l_entreprise = Column(Integer)
    annees_dans_le_poste_actuel = Column(Integer)
    annees_depuis_la_derniere_promotion = Column(Integer)
    annes_sous_responsable_actuel = Column(Integer)
    satisfaction_employee_environnement = Column(Integer)
    note_evaluation_precedente = Column(Integer)
    niveau_hierarchique_poste = Column(Integer)
    satisfaction_employee_nature_travail = Column(Integer)
    satisfaction_employee_equipe = Column(Integer)
    satisfaction_employee_equilibre_pro_perso = Column(Integer)
    note_evaluation_actuelle = Column(Integer)
    augementation_salaire_precedente = Column(Integer)
    nombre_participation_pee = Column(Integer)
    nb_formations_suivies = Column(Integer)
    nombre_employee_sous_responsabilite = Column(Integer)
    distance_domicile_travail = Column(Integer)
    niveau_education = Column(Integer)
    genre = Column(String)
    frequence_deplacement = Column(String)
    poste = Column(String)
    statut_marital = Column(String)
    departement = Column(String)
    domaine_etude = Column(String)
    heure_supplementaires = Column(String)

    # Relation avec la table des sorties
    output = relationship("PredictionOutput", back_populates="input", uselist=False)

class PredictionOutput(Base):
    __tablename__ = "prediction_outputs"

    id = Column(Integer, primary_key=True, index=True)
    input_id = Column(Integer, ForeignKey("prediction_inputs.id"))
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    prediction = Column(Integer)
    churn_probability = Column(Float)
    
    # Relation inverse
    input = relationship("PredictionInput", back_populates="output")