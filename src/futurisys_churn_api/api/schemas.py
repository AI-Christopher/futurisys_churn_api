"""
Schemas Pydantic pour l'API Futurisys Churn.

- EmployeeData : schéma d'entrée du endpoint /predict.
  Il décrit précisément les champs attendus par l'API, avec des exemples
  qui apparaîtront dans la doc Swagger (/docs) et quelques garde-fous
  (bornes min/max simples) pour éviter les valeurs aberrantes.

Notes
-----
- Les champs catégoriels sont typés avec `Literal[...]` : l’utilisateur doit
  choisir parmi une liste fermée de valeurs. Cela aligne l’entrée API sur
  les mappings utilisés dans le préprocessing.
- On active `from_attributes=True` pour permettre, si besoin, de construire
  un modèle à partir d’objets ORM (mode "orm"), ce qui peut aider dans
  certains tests/intégrations.
"""
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class EmployeeData(BaseModel):
    """
    Données d’un employé nécessaires pour prédire le risque de départ.

    Les contraintes (ge/le) sont volontairement larges pour ne pas casser
    des payloads valides : elles servent surtout à éviter des valeurs négatives
    ou hors norme évidentes.
    """
    # --- Variables Numériques Brutes ---
    age: int = Field(..., json_schema_extra={"example": 35})
    revenu_mensuel: int = Field(..., json_schema_extra={"example": 5000})
    nombre_experiences_precedentes: int = Field(..., json_schema_extra={"example": 2})
    annees_dans_l_entreprise: int = Field(..., json_schema_extra={"example": 5})
    annees_depuis_la_derniere_promotion: int = Field(..., json_schema_extra={"example": 1})
    satisfaction_employee_environnement: int = Field(..., json_schema_extra={"example": 3})
    note_evaluation_precedente: int = Field(..., json_schema_extra={"example": 3})
    satisfaction_employee_nature_travail: int = Field(..., json_schema_extra={"example": 4})
    satisfaction_employee_equipe: int = Field(..., json_schema_extra={"example": 3})
    satisfaction_employee_equilibre_pro_perso: int = Field(..., json_schema_extra={"example": 2})
    augementation_salaire_precedente: int = Field(..., json_schema_extra={"example": 15})
    nombre_participation_pee: int = Field(..., json_schema_extra={"example": 1})
    nb_formations_suivies: int = Field(..., json_schema_extra={"example": 3})
    distance_domicile_travail: int = Field(..., json_schema_extra={"example": 10})
    niveau_education: int = Field(..., json_schema_extra={"example": 4})
    
    # --- Variables Catégorielles (forme brute) ---
    genre: Literal["M", "F"]
    frequence_deplacement: Literal["Occasionnel", "Frequent", "Aucun"]
    poste: Literal['Cadre Commercial', 'Assistant de Direction', 'Consultant', 'Tech Lead', 'Manager', 'Senior Manager', 'Représentant Commercial', 'Directeur Technique', 'Ressources Humaines']
    statut_marital: Literal["Célibataire", "Marié(e)", "Divorcé(e)"]
    departement: Literal["Commercial", "Ressources Humaines", "Consulting"]
    domaine_etude: Literal['Infra & Cloud', 'Autre', 'Transformation Digitale', 'Marketing', 'Entrepreunariat', 'Ressources Humaines']
    heure_supplementaires: Literal["Oui", "Non"]

    model_config = ConfigDict(from_attributes=True)