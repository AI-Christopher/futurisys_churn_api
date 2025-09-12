"""
Point d’entrée FastAPI de l’API Futurisys Churn (sans rate limiting).

Ce module :
- crée l’application FastAPI (titre, description, version),
- configure la CORS,
- branche les routeurs `auth` et `prediction`,
- expose des endpoints de santé ("/" et "/health").

⚠️ En production, remplace `allow_origins=["*"]` par la liste des domaines front autorisés.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .endpoints import prediction, auth  # Routes métier

# -- Métadonnées de l’API (affichées dans /docs)
app = FastAPI(
    title="Futurisys Turnover Prediction API",
    description="API pour prédire la probabilité de démission d'un employé.",
    version="0.1.0",
)

# -- CORS (qui peut appeler l’API ?)
# En dev on autorise tout. En prod, restreindre aux domaines connus.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # ex. ["https://ton-front.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Routeurs
app.include_router(auth.router)        # /auth/...
app.include_router(prediction.router)  # /predict

# -- Endpoints de santé
@app.get("/", tags=["Health"])
def read_root() -> dict[str, str]:
    """Ping lisible par humain."""
    return {"message": "API de prédiction de turnover - Futurisys"}

@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    """Endpoint de santé pour monitoring."""
    return {"status": "ok"}
