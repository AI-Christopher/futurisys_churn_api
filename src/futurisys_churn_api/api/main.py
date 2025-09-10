from fastapi import FastAPI
from .endpoints import prediction, auth
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse


app = FastAPI(
    title="Futurisys Turnover Prediction API",
    description="API pour prédire la probabilité de démission d'un employé.",
    version="0.1.0",
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request, exc):
    return PlainTextResponse("Too Many Requests", status_code=429)

# CORS — adapte aux domaines front autorisés :
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permet à tout le monde de se connecter (OK pour le dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

app.include_router(prediction.router)

@app.get("/")
def read_root():
    return {"message": "API de prédiction de turnover - Futurisys"}