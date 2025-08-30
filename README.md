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

# API de Prédiction de Turnover - Futurisys

Ce projet a pour objectif de déployer un modèle de machine learning capable de prédire la probabilité qu'un employé démissionne. L'accès au modèle se fait via une API RESTful performante.

## Contexte

Projet réalisé dans le cadre d'une mission freelance pour Futurisys, visant à industrialiser un modèle de classification pré-existant.

## Structure du Projet

Le projet est organisé comme suit :
- `/api`: Contient le code source de l'application FastAPI.
- `/models`: Stocke le modèle de classification sérialisé.
- `/scripts`: Scripts pour l'entraînement et l'évaluation du modèle.
- `/tests`: Tests unitaires et d'intégration.

## Installation

1.  **Cloner le dépôt :**
    ```bash
    git clone https://github.com/[TonNomUtilisateur]/futurisys_churn_api.git
    cd futurisys_churn_api
    ```

2.  **Créer et activer l'environnement virtuel :**
    ```bash
    uv init
    source .venv/bin/activate  # macOS/Linux
    # .venv\Scripts\activate  # Windows
    ```

3.  **Installer les dépendances :**
    ```bash
    uv pip install -r requirements.txt
    ```

## Utilisation

Pour lancer l'API en local, exécutez la commande suivante depuis la racine du projet :
```bash
uvicorn api.main:app --reload

L'API sera accessible à l'adresse http://127.0.0.1:8000. La documentation interactive (Swagger UI) se trouve à http://127.0.0.1:8000/docs.

## Workflow Git
Ce projet utilise le workflow Git Flow.
 * main: Contient le code en production.
 * develop: Branche d'intégration pour les nouvelles fonctionnalités.
 * Les nouvelles fonctionnalités sont développées dans des branches feature/*.