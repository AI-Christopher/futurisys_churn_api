from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de connexion à la base. Remplace avec tes propres informations.
# Format: "postgresql://utilisateur:mot_de_passe@hote:port/nom_db"
DATABASE_URL = "postgresql://postgres:Azerty1234@localhost:5432/futurisys_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()