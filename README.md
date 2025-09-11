---
title: Futurisys Churn API
emoji: 🌍
colorFrom: pink
colorTo: gray
sdk: docker
pinned: false
license: mit
short_description: API de détection des démissionnaires
---

<a id="readme-top"></a>

[![CI](https://img.shields.io/github/actions/workflow/status/AI-Christopher/futurisys_churn_api/ci-pipeline.yml?label=CI%2FCD)](https://github.com/AI-Christopher/futurisys_churn_api/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)

# Futurisys Churn API

Service d’inférence **FastAPI** exposant un modèle **XGBoost** pour prédire le risque de départ (churn) d’employés.  
Le modèle est servi via une API REST performante et documentée automatiquement (OpenAPI/Swagger). Le pipeline CI/CD automatise les tests et le déploiement (Hugging Face Spaces).

## Sommaire
- [À propos](#à-propos)
- [Stack technique](#stack-technique-built-with)
- [Structure du dépôt](#structure-du-dépôt)
- [Démarrage rapide](#démarrage-rapide)
- [Configuration](#configuration)
- [Authentification & Sécurité](#authentification--sécurité)
- [Usage](#usage)
- [Modèle & Performances](#modèle--performances)
- [Schéma de requête & Features](#schéma-de-requête--features)
- [Architecture & Données](#architecture--données)
- [Tests & Qualité](#tests--qualité)
- [CI/CD & Déploiement](#cicd--déploiement)
- [Dépannage (FAQ)](#dépannage-faq)
- [Roadmap](#roadmap)
- [Contribuer](#contribuer)
- [Licence](#licence)

## À propos
- **Sorties** : `prediction` (0/1) + `churn_probability` (0.0–1.0).
- **Traçabilité** : persistance **optionnelle** (local) des entrées/sorties en base via **SQLAlchemy** ; désactivée par défaut en déploiement (HF Spaces).
- **Déploiement** : Docker + GitHub Actions (+ Hugging Face Spaces).

### Stack technique (Built With)
- **API** : FastAPI, Uvicorn
- **Validation** : Pydantic
- **ML** : XGBoost, scikit-learn, joblib
- **DB (optionnelle)** : SQLAlchemy (PostgreSQL/SQLite)
- **Sécurité** : OAuth2/JWT (scopes & rôles), option **X-API-Key**
- **Qualité** : pytest, coverage, ruff
- **Packaging** : uv, pyproject.toml
- **CI/CD** : GitHub Actions
- **Conteneurisation** : Docker

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Structure du dépôt

```
.
├─ .github/workflows/
│  └─ ci-pipeline.yml           # CI/CD : lint, tests, build, déploiement
├─ models/
│  ├─ churn_model.joblib        # Modèle entraîné
│  └─ input_features.json       # Features attendues par le modèle (post-preprocessing)
├─ src/futurisys_churn_api/
│  ├─ api/
│  │  ├─ endpoints/
│  │  │  ├─ prediction.py       # Endpoint /predict
│  │  │  └─ auth.py             # Endpoints /auth/* (si activés)
│  │  ├─ constants.py           # Mappings catégoriels
│  │  ├─ preprocessing.py       # Encodage & features dérivées
│  │  ├─ schemas.py             # Schémas Pydantic (requêtes)
│  │  ├─ security.py            # JWT, scopes, user factice (mode sans BDD), X-API-Key
│  │  └─ main.py                # App FastAPI + CORS
│  ├─ database/
│  │  ├─ connection.py          # Connexion SQLAlchemy (PostgreSQL/SQLite), toggle via env
│  │  └─ models.py              # ORM (PredictionInput/Output, User si activé)
│  └─ tests/                    # Tests API, DB, preprocessing
├─ docs/
│  ├─ er_diagram.png            # Diagramme ER
│  └─ architecture_diagram.png  # Schéma d'architecture
├─ Dockerfile
├─ pyproject.toml
├─ requirements.txt
└─ README.md
```

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Démarrage rapide

### Prérequis
- Python **3.12+**
- **uv** (gestion d’env) → `pip install uv`
- (Optionnel) **PostgreSQL** 14+ (ou SQLite)
- (Optionnel) **Docker** 24+

### Installation
```bash
git clone https://github.com/AI-Christopher/futurisys_churn_api.git
cd futurisys_churn_api

uv venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

uv sync
```

### Lancer l’API
```bash
python -m uvicorn futurisys_churn_api.api.main:app --reload
# Swagger: http://127.0.0.1:8000/docs
```

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Configuration

Variables d’environnement principales :
```bash
# Persistance BDD (désactivée pour HF Spaces)
export DATABASE_ENABLED=false

# URL BDD (PostgreSQL ou SQLite). Exemple Postgres :
export DATABASE_URL="postgresql://postgres:<password>@localhost:5432/futurisys_db"

# Sécurité JWT
export JWT_SECRET_KEY="change-me-in-prod"
export JWT_EXPIRE_MINUTES=60

# (Optionnel) Garde-fou par clé API (en plus du JWT)
export API_KEY="secret123"   # si défini, /predict exige: X-API-Key: secret123
```

> **Note CORS** : par défaut, `main.py` autorise `https://ton-frontend.example`. Adapte `allow_origins` selon ton front.

### Base de données (local)
- Activer : `DATABASE_ENABLED=true`
- Choisir le SGBD via `DATABASE_URL` :  
  - **Postgres** : `postgresql://user:pwd@host:5432/dbname`  
  - **SQLite** : `sqlite:///chemin/vers/db.sqlite3`

```bash
# Pour créer la base et les tables (la première fois)
python -m futurisys_churn_api.database.create_db 

# Pour effacer et recréer les tables (après une modification du modèle de données)
python -m futurisys_churn_api.database.create_db --recreate 

# Permet de remplis les tables, avec un jeu de données initial ou à chaque réinitialisation de la BDD
python -m futurisys_churn_api.database.seed_db 

# Génère les predictions des données insérées
python -m futurisys_churn_api.database.batch_predict 
```

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Authentification & Sécurité

> **Note** : la section *Authentification & Sécurité* décrit une mise en place standard (JWT + API Key). Si votre code actuel n’inclut pas encore les endpoints `/auth/*` ni le modèle `users`, considérez cette section comme **proposée** et à activer ultérieurement.


### 1) JWT (OAuth2 Password Flow)
- `POST /auth/token` : obtient un access token (Bearer) depuis username/password.
- Scopes par rôle (exemple) :  
  - `viewer` → `predict:read`  
  - `analyst` → `predict:read`, `predict:write`  
  - `admin` → `predict:read`, `predict:write`, `admin`

**Mode sans BDD (dev/tests)** : utilisateur factice disponible.  
`username=futurisys_user`, `password=futurisys_password` (si fourni par le module `security.py`).

**Mode avec BDD** :  
- `POST /auth/register` : créer un utilisateur.  
- `POST /auth/token` : login avec l’email/pass enregistrés.

### 2) Clé API (optionnelle)
Si `API_KEY` est définie, les requêtes protégées (ex. `/predict`) exigent **en plus** du Bearer token :
```
X-API-Key: <valeur_de_API_KEY>
```

### 3) Bonnes pratiques
- Ne committe jamais de secrets (utiliser GitHub Secrets).
- Mots de passe hashés (bcrypt via `passlib[bcrypt]`).
- Scopes sur les endpoints sensibles (ex. `predict:read`).
- Journalise les accès (sans PII).

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Usage

### 1) Obtenir un token
**Sans BDD (dev/tests)** :
```bash
curl -X POST http://127.0.0.1:8000/auth/token      -H "Content-Type: application/x-www-form-urlencoded"      -d "username=futurisys_user&password=futurisys_password"
# → {"access_token":"<JWT>", "token_type":"bearer"}
```

**Avec BDD** :
```bash
# (une seule fois) créer un utilisateur
curl -X POST "http://127.0.0.1:8000/auth/register?email=u1@test.com&password=pw"

# puis login
curl -X POST http://127.0.0.1:8000/auth/token      -H "Content-Type: application/x-www-form-urlencoded"      -d "username=u1@test.com&password=pw"
```

### 2) Appeler `/predict`
```bash
TOKEN="<access_token_reçu>"
# Si API_KEY est définie :
API_KEY="secret123"

curl -X POST http://127.0.0.1:8000/predict   -H "Authorization: Bearer $TOKEN"   -H "Content-Type: application/json"   -H "X-API-Key: $API_KEY"   -d '{
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

**Réponse (sans BDD)** :
```json
{"prediction":0,"churn_probability":0.17}
```

**Réponse (avec BDD)** :
```json
{"prediction_id":124,"input_id":123,"prediction":0,"churn_probability":0.17}
```

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Modèle & Performances

- **Modèle** : XGBoost (sauvegardé via joblib)  
- **Contrat d’interface** : `models/input_features.json` (liste ordonnée des features post-préprocessing)

**Exemple de métriques (jeu de test)** :  
- F1 (classe 1) : **0.54**  
- Recall (classe 1) : **0.56**  
- Precision (classe 1) : **0.52**  
- Accuracy : **0.87**

### Maintenance
- Surveiller les performances réelles (si vérité terrain disponible).
- Ré-entraîner tous les 6 mois ou si dérive détectée.
- Versionner : `churn_model_vX.Y.joblib`.

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Schéma de requête & Features

### Champs d’entrée (Pydantic)

**Numériques**

| Champ | Type |
|---|---|
| `age` | int |
| `revenu_mensuel` | int |
| `nombre_experiences_precedentes` | int |
| `annee_experience_totale` | int |
| `annees_dans_l_entreprise` | int |
| `annees_dans_le_poste_actuel` | int |
| `annees_depuis_la_derniere_promotion` | int |
| `annes_sous_responsable_actuel` | int |
| `satisfaction_employee_environnement` | int |
| `note_evaluation_precedente` | int |
| `niveau_hierarchique_poste` | int |
| `satisfaction_employee_nature_travail` | int |
| `satisfaction_employee_equipe` | int |
| `satisfaction_employee_equilibre_pro_perso` | int |
| `note_evaluation_actuelle` | int |
| `augementation_salaire_precedente` | int |
| `nombre_participation_pee` | int |
| `nb_formations_suivies` | int |
| `nombre_employee_sous_responsabilite` | int |
| `distance_domicile_travail` | int |
| `niveau_education` | int |

**Catégoriels**

| Champ | Valeurs autorisées |
|---|---|
| `genre` | `M` | `F` |
| `frequence_deplacement` | `Occasionnel` | `Frequent` | `Aucun` |
| `poste` | `Cadre Commercial` | `Assistant de Direction` | `Consultant` | `Tech Lead` | `Manager` | `Senior Manager` | `Représentant Commercial` | `Directeur Technique` | `Ressources Humaines` |
| `statut_marital` | `Célibataire` | `Marié(e)` | `Divorcé(e)` |
| `departement` | `Commercial` | `Ressources Humaines` | `Consulting` |
| `domaine_etude` | `Infra & Cloud` | `Autre` | `Transformation Digitale` | `Marketing` | `Entrepreunariat` | `Ressources Humaines` |
| `heure_supplementaires` | `Oui` | `Non` |

> Remarque : le preprocessing accepte aussi `"Fréquent"` (accentué), tandis que le schéma Pydantic autorise `"Frequent"` (non accentué). Harmonisez selon votre choix.

### Features modèle (liste exacte)
*(post-préprocessing — inclut variables dérivées & OHE)*

- `satisfaction_employee_nature_travail`
- `satisfaction_employee_environnement`
- `heure_supplementaires`
- `satisfaction_employee_equilibre_pro_perso`
- `age`
- `note_evaluation_precedente`
- `frequence_deplacement`
- `poste`
- `genre`
- `annees_dans_l_entreprise`
- `nombre_participation_pee`
- `distance_domicile_travail`
- `satisfaction_employee_equipe`
- `statut_marital_Divorce`
- `nb_formations_suivies`
- `augementation_salaire_precedente`
- `statut_marital_Marie`
- `domaine_etude_TransformationDigitale`
- `departement_Consulting`
- `revenu_satisfaction`
- `niveau_education`
- `ratio_revenu_poste`
- `ratio_augmentation_promotion`
- `domaine_etude_Marketing`
- `domaine_etude_Entrepreunariat`

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Architecture & Données

### Flux (simplifié)
```
Client -> FastAPI (/predict) -> preprocessing.py -> modèle (joblib)
                                  |                      |
                                  +--(si activé)------> Base SQL (inputs/outputs, users si activé)
```

### Diagrammes
- **ER** : ![ER](docs/er_diagram.png)

> Si vous copiez ce README, pensez à placer les images dans le dossier `docs/` du dépôt.

### Schéma BDD (mode persistance)
- `prediction_inputs` : tous les champs d’entrée + `id`
- `prediction_outputs` : `id`, `input_id` (FK), `user_id` (FK), `timestamp`, `prediction`, `churn_probability`
- `users` : id, email (unique), hashed_password, role (viewer|analyst|admin), is_active (si activé)

Relations :  
- `prediction_inputs (1)` —— `prediction_outputs (1)`  
- `users (1)` —— `(n) prediction_outputs` (si activé)

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Tests & Qualité
```bash
# Tests + couverture
uv run pytest --cov=futurisys_churn_api --cov-report=term-missing

# Lint (Ruff)
uv run ruff check src/ tests/ --fix
```
Couverture visée ≥ **80%**.

```bash
Name                                                  Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------------------------------------------
src\futurisys_churn_api\api\constants.py                  3      0      0      0   100%
src\futurisys_churn_api\api\endpoints\auth.py            36      1     16      2    94%   20, 40->43
src\futurisys_churn_api\api\endpoints\prediction.py      58      7      6      1    88%   69-70, 79-80, 87->90, 110-112
src\futurisys_churn_api\api\main.py                      19      1      0      0    95%   21
src\futurisys_churn_api\api\preprocessing.py             36      1      8      1    95%   28
src\futurisys_churn_api\api\schemas.py                   27      0      0      0   100%
src\futurisys_churn_api\api\security.py                  59      5     22      4    89%   67-69, 76->79, 80, 84
src\futurisys_churn_api\database\connection.py           21      0      4      0   100%
src\futurisys_churn_api\database\models.py               51      0      0      0   100%
-------------------------------------------------------------------------------------------------
TOTAL                                                   310     15     56      8    94%
Required test coverage of 80% reached. Total coverage: 93.72%
```
<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## CI/CD & Déploiement
- GitHub Actions : `.github/workflows/ci-pipeline.yml`  
  Ruff → Pytest (coverage) → Build Docker → (option) déploiement HF Spaces.

**Secrets** :  
- `HF_TOKEN` (déploiement Hugging Face Spaces)

**Prod (Spaces)** :  
- `DATABASE_ENABLED=false` (pas de persistance)  
- Définir `JWT_SECRET_KEY`  
- (Optionnel) `API_KEY` pour exiger `X-API-Key`

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Dépannage (FAQ)

**Erreur `trapped) error reading bcrypt version` au démarrage**  
Mettre à jour/installer les paquets liés à bcrypt :
```bash
pip install --upgrade "bcrypt>=4.0.0" "passlib[bcrypt]" --only-binary=bcrypt
```
> Sous Windows, éviter les versions obsolètes de `bcrypt`.

**Appels `/predict` renvoient 401**  
- Obtenez d’abord un token via `/auth/token` et envoyez `Authorization: Bearer <token>`.
- Si `API_KEY` est définie, ajoutez aussi `X-API-Key: <valeur>`.

**Clé API activée mais toujours 200 sans l’en-tête**  
- Redémarrez l’app après avoir défini `API_KEY` (les serveurs prod lisent l’env au démarrage).

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Roadmap
- Monitoring de dérive (data & concept) et alerting
- Pipeline de ré-entraînement versionné
- Observabilité (logs structurés, métriques)
- Hardening : quotas/rate limiting, journaux d’audit
- Exports automatiques pour BI (si persistance activée)

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Contribuer
Les contributions sont bienvenues !
1. Forker le dépôt
2. Créer une branche : `git checkout -b feature/ma-feature`
3. Commit : `git commit -m "feat: ajoute ma feature"`
4. Push : `git push origin feature/ma-feature`
5. Ouvrir une Pull Request

<p align="right">(<a href="#readme-top">retour en haut</a>)</p>

## Licence
MIT
