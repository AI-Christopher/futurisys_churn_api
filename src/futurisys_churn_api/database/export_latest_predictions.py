from sqlalchemy.orm import sessionmaker
from futurisys_churn_api.database.connection import engine
from futurisys_churn_api.database.models import PredictionOutput
import pandas as pd, os

def main():
    if engine is None:
        print("DATABASE_ENABLED=false → export désactivé.")
        return
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as s:
        rows = s.query(PredictionOutput).order_by(PredictionOutput.timestamp.desc()).all()
        if not rows:
            print("Aucune prédiction à exporter.")
            return
        df = pd.DataFrame([{
            "id": r.id,
            "input_id": r.input_id,
            "user_id": r.user_id,
            "timestamp": r.timestamp,
            "prediction": r.prediction,
            "churn_probability": r.churn_probability,
        } for r in rows])
        os.makedirs("exports", exist_ok=True)
        out = "exports/predictions.csv"
        df.to_csv(out, index=False)
        print(f"Export OK → {out}")

if __name__ == "__main__":
    main()
