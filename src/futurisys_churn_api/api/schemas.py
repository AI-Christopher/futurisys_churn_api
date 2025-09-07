from pydantic import BaseModel, Field
from typing import Literal

# Ce modèle Pydantic définit la structure des données que l'API attend
class EmployeeData(BaseModel):
    # --- Variables Numériques Brutes ---
    # On utilise Field pour ajouter des exemples qui apparaîtront dans la doc
    age: int = Field(..., json_schema_extra={"example": 35})
    revenu_mensuel: int = Field(..., json_schema_extra={"example": 5000})
    nombre_experiences_precedentes: int = Field(..., json_schema_extra={"example": 2})
    annee_experience_totale: int = Field(..., json_schema_extra={"example": 10})
    annees_dans_l_entreprise: int = Field(..., json_schema_extra={"example": 5})
    annees_dans_le_poste_actuel: int = Field(..., json_schema_extra={"example": 3})
    annees_depuis_la_derniere_promotion: int = Field(..., json_schema_extra={"example": 1})
    annes_sous_responsable_actuel: int = Field(..., json_schema_extra={"example": 2})
    satisfaction_employee_environnement: int = Field(..., json_schema_extra={"example": 3})
    note_evaluation_precedente: int = Field(..., json_schema_extra={"example": 3})
    niveau_hierarchique_poste: int = Field(..., json_schema_extra={"example": 2})
    satisfaction_employee_nature_travail: int = Field(..., json_schema_extra={"example": 4})
    satisfaction_employee_equipe: int = Field(..., json_schema_extra={"example": 3})
    satisfaction_employee_equilibre_pro_perso: int = Field(..., json_schema_extra={"example": 2})
    note_evaluation_actuelle: int = Field(..., json_schema_extra={"example": 4})
    augementation_salaire_precedente: int = Field(..., json_schema_extra={"example": 15})
    nombre_participation_pee: int = Field(..., json_schema_extra={"example": 1})
    nb_formations_suivies: int = Field(..., json_schema_extra={"example": 3})
    nombre_employee_sous_responsabilite: int = Field(..., json_schema_extra={"example": 4})
    distance_domicile_travail: int = Field(..., json_schema_extra={"example": 10})
    niveau_education: int = Field(..., json_schema_extra={"example": 4})
    
    # --- Variables Catégorielles (forme brute) ---
    # On utilise Literal pour forcer l'utilisateur à choisir parmi des valeurs fixes.
    genre: Literal["M", "F"]
    frequence_deplacement: Literal["Occasionnel", "Frequent", "Aucun"]
    poste: Literal['Cadre Commercial', 'Assistant de Direction', 'Consultant', 'Tech Lead', 'Manager', 'Senior Manager', 'Représentant Commercial', 'Directeur Technique', 'Ressources Humaines']
    statut_marital: Literal["Célibataire", "Marié(e)", "Divorcé(e)"]
    departement: Literal["Commercial", "Ressources Humaines", "Consulting"]
    domaine_etude: Literal['Infra & Cloud', 'Autre', 'Transformation Digitale', 'Marketing', 'Entrepreunariat', 'Ressources Humaines']
    heure_supplementaires: Literal["Oui", "Non"]

class Config:
        # Cette option permet à Pydantic de créer un modèle à partir d'objets non-dict
        from_attributes = True