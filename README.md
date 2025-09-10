---
title: Futurisys Churn Api
emoji: 🌍
colorFrom: pink
colorTo: gray
sdk: docker
pinned: false
license: mit
short_description: API de détection des démissionnaire
---

# API de Prédiction de Turnover - Futurisys (v1.0.0)

Ce projet déploie un modèle de machine learning capable de prédire la probabilité qu'un employé démissionne. L'accès au modèle se fait via une API RESTful performante construite avec FastAPI.

## 1. Architecture et Choix Techniques

Le projet est structuré autour d'un pipeline CI/CD complet, allant du développement local au déploiement automatisé sur Hugging Face Spaces.

- **API :** `FastAPI` pour sa performance et sa documentation automatique (OpenAPI).
- **Validation des données :** `Pydantic` pour une validation robuste des données en entrée.
- **Base de Données :** `PostgreSQL` avec l'ORM `SQLAlchemy` pour la traçabilité des prédictions en environnement local.
- **Gestionnaire de paquets :** `uv` pour sa rapidité.
- **CI/CD :** `GitHub Actions` pour l'intégration et les tests continus.
- **Déploiement :** `Docker` et `Hugging Face Spaces` pour la mise en ligne.
- **Versioning :** `Git Flow` pour une gestion structurée des branches et des versions.

## 2. Le Modèle de Machine Learning

### Objectif
Le modèle a été entraîné pour identifier les employés de **TechNova Partners** les plus susceptibles de démissionner.

### Performance
Le modèle final est un `XGBoost` optimisé. Ses performances sur le jeu de test sont :
- **F1-Score (classe "départ") :** 0.54
- **Rappel :** 0.56 (identifie 56% des vrais départs)
- **Précision :** 0.52 (52% de fiabilité sur les alertes de départ)

### Maintenance et Mise à Jour
Un protocole de mise à jour régulière du modèle est recommandé :
1.  **Surveillance :** Suivre les performances du modèle en production en comparant ses prédictions aux départs réels.
2.  **Ré-entraînement :** Tous les 6 mois (ou si une baisse de performance est détectée), le modèle doit être ré-entraîné sur des données fraîches, en incluant les données des nouvelles requêtes stockées en base.
3.  **Versioning :** Chaque nouveau modèle entraîné doit être versionné (ex: `churn_model_v1.1.joblib`) et déployé via le pipeline CI/CD.

## 3. Installation et Utilisation

### Installation
1.  **Cloner le dépôt :**
    ```bash
    git clone https://github.com/AI-Christopher/futurisys_churn_api.git
    cd futurisys_churn_api
    ```
2.  **Créer et activer l'environnement virtuel :**
    ```bash
    uv venv
    source .venv/bin/activate # ou .venv\Scripts\activate
    ```
3.  **Installer les dépendances (développement inclus) :**
    ```bash
    uv sync
    ```
4. **Création de la BDD et des tables**
    * Pré-requis avoir installé PostgreSQL en local
    ```SQL
    CREATE DATABASE futurisys_db;
    ```
    ```bash
    python -m futurisys_api.scripts.create_db
    ```

### Utilisation Locale
1.  **Activer la BDD**
    ```bash
    export DATABASE_ENABLED=true
    export DATABASE_URL="postgresql://postgres:ton_mot_de_passe@localhost:5432/futurisys_db"
    ```
2.  **Lancer l'API :**
    ```bash
    python -m uvicorn futurisys_churn_api.api.main:app --reload
    ```
3.  **Accéder à la documentation interactive :**
    Ouvrez votre navigateur à l'adresse [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Exemple d'Interaction (avec `curl`)
Voici un exemple de requête vers l'endpoint `/predict` :
```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 35,
    "revenu_mensuel": 5000,
    "nombre_experiences_precedentes": 2,
    "annee_experience_totale": 10,
    "annees_dans_l_entreprise": 5,
    "annees_dans_le_poste_actuel": 3,
    "annees_depuis_la_derniere_promotion": 1,
    "annes_sous_responsable_actuel": 2,
    "satisfaction_employee_environnement": 3,
    "note_evaluation_precedente": 3,
    "niveau_hierarchique_poste": 2,
    "satisfaction_employee_nature_travail": 4,
    "satisfaction_employee_equipe": 3,
    "satisfaction_employee_equilibre_pro_perso": 2,
    "note_evaluation_actuelle": 4,
    "augementation_salaire_precedente": 15,
    "nombre_participation_pee": 1,
    "nb_formations_suivies": 3,
    "nombre_employee_sous_responsabilite": 4,
    "distance_domicile_travail": 10,
    "niveau_education": 4,
    "genre": "F",
    "frequence_deplacement": "Frequent",
    "poste": "Manager",
    "statut_marital": "Marié(e)",
    "departement": "Consulting",
    "domaine_etude": "Transformation Digitale",
    "heure_supplementaires": "Oui"
  }'
  ```

### Exemple de reponse
```bash
{
  "prediction": 0,
  "churn_probability": 0.17,
  "input_id": 123,
  "prediction_id": 124
}
```

### Valeurs catégorielles acceptées (exemples) :
 * **frequence_deplacement**: Aucun, Occasionnel, Frequent
 * **poste**: Cadre Commercial, Assistant de Direction, Consultant, Tech Lead, Manager, Senior Manager, Représentant Commercial, Directeur Technique, Ressources Humaines
Les listes complètes vivent dans api/constants.py.

## 4. Tests et Qualité

Le projet inclut une suite de tests unitaires et fonctionnels utilisant pytest. Pour lancer les tests et générer un rapport de couverture :
```bash
pytest
```
Nous visons une couverture de code d'au moins 80%.

## 5. Déploiement (Hugging Face Space)
 * Le job GitHub Actions deploy pousse main vers le Space.
 * Configurer le secret HF_TOKEN.
 * Voir .github/workflows/…yml.
 * Désactivation de la BDD
```bash
export DATABASE_ENABLED=true
```