from fastapi import FastAPI

app = FastAPI(
    title="Futurisys Turnover Prediction API",
    description="API pour prédire la probabilité de démission d'un employé.",
    version="0.1.0",
)

@app.get("/")
def read_root():
    return {"message": "API de prédiction de turnover - Futurisys"}